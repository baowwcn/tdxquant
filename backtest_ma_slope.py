"""
均线斜率平行策略回测
公式逻辑：
  N = 120
  MA60 = MA(CLOSE, 60)
  MA120 = MA(CLOSE, 120)
  K60 = ROUND2(CONST(SLOPE(MA60, N)), 2)
  K120 = ROUND2(CONST(SLOPE(MA120, N)), 2)
  选股条件：(ABS(K60-K120) <= 0.02 AND K60 > K120) AND K60*K120 >= 0
"""

import sys
import os
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt


def calculate_slope(series, window=120):
    """计算序列滚动窗口的线性回归斜率"""

    def slope_on_window(y):
        if len(y) < 2 or np.any(np.isnan(y)):
            return np.nan
        x = np.arange(len(y))
        slope, _, _, _, _ = stats.linregress(x, y)
        return slope

    return series.rolling(window).apply(slope_on_window, raw=True)


def generate_signals(df, n=120):
    """根据公式生成交易信号"""
    df = df.copy()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["MA120"] = df["Close"].rolling(120).mean()

    df["K60"] = calculate_slope(df["MA60"], window=n)
    df["K120"] = calculate_slope(df["MA120"], window=n)

    df["K60"] = df["K60"].round(2)
    df["K120"] = df["K120"].round(2)

    cond1 = (df["K60"] - df["K120"]).abs() <= 0.02
    cond2 = df["K60"] > df["K120"]
    cond3 = df["K60"] * df["K120"] >= 0
    df["Signal"] = (cond1 & cond2 & cond3).astype(int)

    df["Position"] = df["Signal"].diff()
    df["Buy"] = (df["Position"] == 1).astype(int)
    df["Sell"] = (df["Position"] == -1).astype(int)

    return df


def backtest(df, initial_capital=100000):
    """执行回测"""
    data = df.copy()
    data["Next_Open"] = data["Open"].shift(-1)

    capital = initial_capital
    position = 0
    cash = capital
    trades = []

    for i in range(len(data) - 1):
        if data["Buy"].iloc[i] == 1 and cash > 0:
            buy_price = data["Next_Open"].iloc[i]
            if not np.isnan(buy_price) and buy_price > 0:
                position = cash / buy_price
                cash = 0
                trades.append((data.index[i], "BUY", buy_price, position))

        elif data["Sell"].iloc[i] == 1 and position > 0:
            sell_price = data["Next_Open"].iloc[i]
            if not np.isnan(sell_price) and sell_price > 0:
                cash = position * sell_price
                trades.append((data.index[i], "SELL", sell_price, position))
                position = 0

        if position > 0:
            data.loc[data.index[i], "Total_Value"] = (
                cash + position * data["Close"].iloc[i]
            )
        else:
            data.loc[data.index[i], "Total_Value"] = cash

    if position > 0:
        final_price = data["Close"].iloc[-1]
        cash = position * final_price
        trades.append((data.index[-1], "SELL_FINAL", final_price, position))
        position = 0

    data["Total_Value"] = data["Total_Value"].ffill().fillna(initial_capital)

    return data, trades


def performance_metrics(equity_curve):
    """计算绩效指标"""
    returns = equity_curve.pct_change().dropna()
    if len(returns) == 0:
        return {}

    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    ann_return = (
        (1 + total_return) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
    )
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = (ann_return - 0.02) / ann_vol if ann_vol != 0 else 0

    rolling_max = equity_curve.expanding().max()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    return {
        "累计收益率": f"{total_return:.2%}",
        "年化收益率": f"{ann_return:.2%}",
        "年化波动率": f"{ann_vol:.2%}",
        "夏普比率": f"{sharpe:.2f}",
        "最大回撤": f"{max_drawdown:.2%}",
    }


if __name__ == "__main__":
    stock_code = "000001.SZ"
    db_path = "C:/new_tdx64/PYPlugins/user/a_share_full.db"

    print(f"从SQLite数据库读取 {stock_code} 日线数据...")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql(
        f"SELECT date, open, high, low, close FROM stock_data WHERE code='{stock_code}' ORDER BY date",
        conn,
        parse_dates=["date"],
    )
    conn.close()

    if df.empty:
        print("未找到数据")
        exit()

    df.columns = [c.capitalize() for c in df.columns]
    df = df.set_index("Date").sort_index()

    print(
        f"数据范围: {df.index[0].date()} 至 {df.index[-1].date()}, 共{len(df)}个交易日"
    )

    print("生成交易信号...")
    df = generate_signals(df, n=120)
    df = df.dropna().copy()

    print("执行回测...")
    data, trades = backtest(df, initial_capital=100000)

    equity = data["Total_Value"]

    print("\n===== 回测绩效 =====")
    metrics = performance_metrics(equity)
    for k, v in metrics.items():
        print(f"{k}: {v}")

    print(f"\n共发生 {len(trades)} 笔交易")
    for i, (date, action, price, qty) in enumerate(trades[:10]):
        print(f"  {date.date()} {action} 价格:{price:.2f} 数量:{qty:.0f}")
    if len(trades) > 10:
        print(f"  ... 还有 {len(trades) - 10} 笔交易")

    plt.figure(figsize=(12, 6))
    plt.plot(equity.index, equity, label="Strategy", linewidth=1.5)

    benchmark = 1 + (df["Close"] / df["Close"].iloc[0] - 1)
    plt.plot(benchmark.index, benchmark, label="Buy&Hold", alpha=0.6)

    buy_dates = df[df["Buy"] == 1].index
    plt.scatter(
        buy_dates,
        equity.loc[buy_dates],
        marker="^",
        color="red",
        s=50,
        label="Buy",
    )

    sell_dates = df[df["Sell"] == 1].index
    plt.scatter(
        sell_dates,
        equity.loc[sell_dates],
        marker="v",
        color="green",
        s=50,
        label="Sell",
    )

    plt.title(f"{stock_code} MA Slope Strategy Backtest")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("backtest_result.png", dpi=150)
    print("\nImage saved to backtest_result.png")
    plt.close()

    print("\nBacktest completed")
