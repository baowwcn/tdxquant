"""
均线斜率平行策略回测 - 随机500只A股 (快速版)
"""

import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import random


def calculate_slope_fast(close_series):
    """快速计算斜率"""
    ma60 = close_series.rolling(60).mean()
    ma120 = close_series.rolling(120).mean()

    k60 = []
    k120 = []

    for i in range(len(close_series)):
        if i >= 119:
            y60 = ma60.iloc[i - 119 : i + 1].dropna()
            y120 = ma120.iloc[i - 119 : i + 1].dropna()

            if len(y60) >= 60:
                x = np.arange(len(y60))
                k60.append(np.polyfit(x, y60, 1)[0])
            else:
                k60.append(np.nan)

            if len(y120) >= 120:
                x = np.arange(len(y120))
                k120.append(np.polyfit(x, y120, 1)[0])
            else:
                k120.append(np.nan)
        else:
            k60.append(np.nan)
            k120.append(np.nan)

    return pd.Series(k60, index=close_series.index), pd.Series(
        k120, index=close_series.index
    )


if __name__ == "__main__":
    db_path = "C:/new_tdx64/PYPlugins/user/a_share_full.db"

    print("获取A股列表...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT code FROM stock_data")
    all_stocks = [r[0] for r in cur.fetchall()]
    conn.close()
    print(f"总股票数: {len(all_stocks)}")

    random.seed(42)
    selected_stocks = random.sample(all_stocks, 500)
    print(f"随机抽取: {len(selected_stocks)} 只")

    start_date = "2018-01-01"
    print(f"回测区间: {start_date} 至今")

    results = []
    print("\n开始回测...")

    for idx, stock in enumerate(selected_stocks):
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql(
                f"SELECT date, open, close FROM stock_data WHERE code='{stock}' AND date >= '{start_date}' ORDER BY date",
                conn,
                parse_dates=["date"],
            )
            conn.close()

            if len(df) < 180:
                continue

            df.columns = ["Date", "Open", "Close"]
            df = df.set_index("Date").sort_index()

            k60, k120 = calculate_slope_fast(df["Close"])

            df["K60"] = k60.round(2)
            df["K120"] = k120.round(2)

            cond1 = (df["K60"] - df["K120"]).abs() <= 0.02
            cond2 = df["K60"] > df["K120"]
            cond3 = df["K60"] * df["K120"] >= 0
            df["Signal"] = (cond1 & cond2 & cond3).astype(int)

            df["Position"] = df["Signal"].diff()
            df["Buy"] = (df["Position"] == 1).astype(int)
            df["Sell"] = (df["Position"] == -1).astype(int)

            df = df.dropna(subset=["K60", "K120"])

            if len(df) < 50:
                continue

            df["Next_Open"] = df["Open"].shift(-1)

            capital = 100000
            position = 0
            cash = capital
            equity_curve = []

            for i in range(len(df) - 1):
                if df["Buy"].iloc[i] == 1 and cash > 0:
                    buy_price = df["Next_Open"].iloc[i]
                    if not np.isnan(buy_price) and buy_price > 0:
                        position = cash / buy_price
                        cash = 0

                elif df["Sell"].iloc[i] == 1 and position > 0:
                    sell_price = df["Next_Open"].iloc[i]
                    if not np.isnan(sell_price) and sell_price > 0:
                        cash = position * sell_price
                        position = 0

                equity = cash + position * df["Close"].iloc[i]
                equity_curve.append(equity)

            if position > 0:
                equity_curve.append(position * df["Close"].iloc[-1])
            else:
                equity_curve.append(cash)

            equity_series = pd.Series(equity_curve, index=df.index[: len(equity_curve)])

            total_return = (equity_series.iloc[-1] / capital) - 1
            returns = equity_series.pct_change().dropna()

            if len(returns) > 0:
                ann_return = (1 + total_return) ** (252 / len(returns)) - 1
                ann_vol = returns.std() * np.sqrt(252)
                sharpe = (ann_return - 0.02) / ann_vol if ann_vol > 0 else 0

                rolling_max = equity_series.expanding().max()
                drawdown = (equity_series - rolling_max) / rolling_max
                max_drawdown = drawdown.min()

                buy_count = df["Buy"].sum()

                results.append(
                    {
                        "stock": stock,
                        "trades": int(buy_count),
                        "total_return": total_return,
                        "ann_return": ann_return,
                        "sharpe": sharpe,
                        "max_drawdown": max_drawdown,
                    }
                )

            if (idx + 1) % 50 == 0:
                print(f"  已完成 {idx + 1}/500, 有效结果: {len(results)}")

        except Exception as e:
            continue

    print(f"\n成功回测: {len(results)} 只股票")

    if results:
        results_df = pd.DataFrame(results)

        print("\n===== 总体统计 =====")
        print(f"平均收益率: {results_df['total_return'].mean():.2%}")
        print(f"平均年化收益率: {results_df['ann_return'].mean():.2%}")
        print(f"平均夏普比率: {results_df['sharpe'].mean():.2f}")
        print(f"平均最大回撤: {results_df['max_drawdown'].mean():.2%}")
        print(f"正收益股票占比: {(results_df['total_return'] > 0).mean():.2%}")

        print("\n===== Top 10 收益 =====")
        top10 = results_df.nlargest(10, "total_return")
        for _, r in top10.iterrows():
            print(
                f"  {r['stock']} 收益:{r['total_return']:.2%} 年化:{r['ann_return']:.2%} 交易:{r['trades']}"
            )

        print("\n===== Bottom 10 收益 =====")
        bottom10 = results_df.nsmallest(10, "total_return")
        for _, r in bottom10.iterrows():
            print(
                f"  {r['stock']} 收益:{r['total_return']:.2%} 年化:{r['ann_return']:.2%}"
            )

        plt.figure(figsize=(12, 6))
        plt.hist(results_df["total_return"], bins=50, edgecolor="black", alpha=0.7)
        plt.axvline(x=0, color="red", linestyle="--", label="Break Even")
        plt.xlabel("Total Return")
        plt.ylabel("Count")
        plt.title("500 A-Stocks Backtest Return Distribution (2018-2026)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.savefig("backtest_500_stocks.png", dpi=150)
        print("\n图片已保存: backtest_500_stocks.png")
        plt.close()

        results_df.to_csv("backtest_results.csv", index=False)
        print("结果已保存: backtest_results.csv")
