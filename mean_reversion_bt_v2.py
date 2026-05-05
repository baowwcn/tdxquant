"""
均值回归策略回测 - 完整版
布林带下轨突破 + ConnorsRSI 超卖
使用 vectorbt 进行专业回测
"""

import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import numpy as np
import pandas as pd
import vectorbt as vbt

tq.initialize('dummy.py')

# 参数
BB_PERIOD = 20
BB_STD = 2
CRSI_RSI_PERIOD = 3
CRSI_STREAK_PERIOD = 2
CRSI_RANK_PERIOD = 100
CRSI_OVERSOLD = 30

def get_stock_list():
    stocks = tq.get_stock_list(market='0', list_type=0)
    sh_stocks = tq.get_stock_list(market='1', list_type=0)
    return [s for s in stocks + sh_stocks if s.startswith(('0','3','6'))][:500]

def calculate_bollinger_bands(close):
    bb_ma = close.rolling(BB_PERIOD).mean()
    bb_std = close.rolling(BB_PERIOD).std()
    bb_upper = bb_ma + BB_STD * bb_std
    bb_lower = bb_ma - BB_STD * bb_std
    return bb_ma, bb_upper, bb_lower

def calculate_connors_rsi(close):
    delta = close.diff()

    # 1. 经典RSI
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(CRSI_RSI_PERIOD).mean()
    avg_loss = loss.rolling(CRSI_RSI_PERIOD).mean()
    rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 1e-9)))

    # 2. 连续涨跌RSI
    sign_diff = np.sign(delta)
    streak = sign_diff.groupby((sign_diff != sign_diff.shift()).cumsum()).cumsum()

    def streak_rsi_calc(x):
        wins = x.clip(lower=0).sum()
        losses = (-x.clip(upper=0)).sum()
        if losses == 0:
            return 50
        return 100 - (100 / (1 + wins / losses))

    streak_rsi = streak.rolling(CRSI_STREAK_PERIOD).apply(streak_rsi_calc)

    # 3. 百分位排名
    roc = close.pct_change()
    rank = roc.rolling(CRSI_RANK_PERIOD).apply(lambda x: pd.Series(x).rank().iloc[-1] / len(x) * 100)

    crsi = (rsi + streak_rsi.fillna(50) + rank.fillna(50)) / 3
    return crsi

def run_backtest():
    stocks = get_stock_list()
    print(f"股票池: {len(stocks)} 只")

    all_results = []
    all_pfs = {}

    for i, stock in enumerate(stocks[:50]):
        print(f"[{i+1}/50] {stock}")
        try:
            df = tq.get_market_data(['Close','Open','High','Low','Volume'], [stock], '1d', dividend_type='none', count=1000)
            if 'Close' not in df or stock not in df['Close']:
                continue

            close = df['Close'][stock]
            open_p = df['Open'][stock]

            if len(close) < 200:
                continue

            # 计算指标
            bb_ma, bb_upper, bb_lower = calculate_bollinger_bands(close)
            crsi = calculate_connors_rsi(close)

            # 信号
            entry_signal = (crsi < CRSI_OVERSOLD) & (open_p < bb_lower)
            exit_signal = open_p < bb_lower

            # 移位：次日执行
            entries = entry_signal.shift(1).fillna(False).to_numpy()
            exits = exit_signal.shift(1).fillna(False).to_numpy()

            # vectorbt回测
            pf = vbt.Portfolio.from_signals(
                close=open_p,
                entries=entries,
                exits=exits,
                init_cash=100000,
                fees=0.001,
                slippage=0.002,
                freq='1d'
            )

            stats = pf.stats()
            if stats['total_return'] > 0:
                all_results.append({
                    'stock': stock,
                    'trades': stats['total_trades'],
                    'return': stats['total_return'],
                    'max_drawdown': stats['max_drawdown'],
                    'win_rate': stats['win_rate'],
                    'profit_factor': stats['profit_factor']
                })
                all_pfs[stock] = pf

        except Exception as e:
            print(f"  Error: {e}")
            continue

    if not all_results:
        print("无有效结果")
        return

    df_result = pd.DataFrame(all_results)
    print("\n" + "="*60)
    print("=== 回测结果 (50只股票, 1000天历史数据) ===")
    print("="*60)
    print(f"正收益股票数: {len(all_results)}/{len(stocks[:50])}")
    print(f"平均收益率: {df_result['return'].mean():.2%}")
    print(f"平均最大回撤: {df_result['max_drawdown'].mean():.2%}")
    print(f"平均胜率: {df_result['win_rate'].mean():.2%}")
    print(f"平均盈亏比: {df_result['profit_factor'].mean():.2f}")

    print("\n=== Top 10 收益 ===")
    print(df_result.nlargest(10, 'return')[['stock','trades','return','max_drawdown','win_rate','profit_factor']])

    # 累计收益曲线
    print("\n=== 汇总统计 ===")
    total_return = df_result['return'].sum()
    avg_trades = df_result['trades'].mean()
    print(f"累计收益率: {total_return:.2%}")
    print(f"平均交易次数: {avg_trades:.1f}")

if __name__ == '__main__':
    run_backtest()
    tq.close()