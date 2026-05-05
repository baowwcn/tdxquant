"""
均值回归策略回测
布林带下轨突破 + ConnorsRSI 超卖
"""

import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import numpy as np
import pandas as pd
import datetime

tq.initialize('dummy.py')

# 参数
BB_PERIOD = 20
BB_STD = 2
CRSI_RSI_PERIOD = 3
CRSI_STREAK_PERIOD = 2
CRSI_RANK_PERIOD = 100
CRSI_OVERSOLD = 30

def get_stock_list():
    """获取A股列表"""
    stocks = tq.get_stock_list(market='0', list_type=0)
    sh_stocks = tq.get_stock_list(market='1', list_type=0)
    return [s for s in stocks + sh_stocks if s.startswith(('0','3','6'))][:500]

def calculate_bollinger_bands(df):
    """计算布林带"""
    close = df['Close']
    df = df.copy()
    df['BB_MA'] = close.rolling(BB_PERIOD).mean()
    df['BB_Upper'] = df['BB_MA'] + BB_STD * close.rolling(BB_PERIOD).std()
    df['BB_Lower'] = df['BB_MA'] - BB_STD * close.rolling(BB_PERIOD).std()
    return df

def calculate_connors_rsi(df):
    """计算ConnorsRSI"""
    df = df.copy()
    close = df['Close']

    # 1. 经典RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(CRSI_RSI_PERIOD).mean()
    avg_loss = loss.rolling(CRSI_RSI_PERIOD).mean()
    rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 1e-9)))

    # 2. 连续涨跌RSI
    sign_diff = np.sign(delta)
    streak = sign_diff.groupby((sign_diff != sign_diff.shift()).cumsum()).cumsum()
    streak_rsi = streak.rolling(CRSI_STREAK_PERIOD).apply(
        lambda x: 100 - (100 / (1 + x.clip(lower=0).sum() / (-x.clip(upper=0).sum() + 1e-9)))
    )

    # 3. 百分位排名
    roc = close.pct_change()
    rank = roc.rolling(CRSI_RANK_PERIOD).apply(lambda x: pd.Series(x).rank().iloc[-1] / len(x) * 100)

    df['ConnorsRSI'] = (rsi + streak_rsi.fillna(50) + rank.fillna(50)) / 3
    return df

def backtest_stock(stock_code, count=500):
    """单股票回测"""
    try:
        df = tq.get_market_data(['Close','Open','High','Low'], [stock_code], '1d', dividend_type='none', count=count)
        if 'Close' not in df or stock_code not in df['Close']:
            return None
        close_df = df['Close'][stock_code]
        if len(close_df) < 100:
            return None

        data = pd.DataFrame({'Close': close_df, 'Open': df['Open'][stock_code]})
        data = calculate_bollinger_bands(data)
        data = calculate_connors_rsi(data)

        # 入场信号
        entries = (data['ConnorsRSI'] < CRSI_OVERSOLD) & (data['Open'] < data['BB_Lower'])
        # 出场信号
        exits = data['Open'] < data['BB_Lower']

        return {'entries': entries, 'exits': exits, 'data': data}
    except:
        return None

def run_backtest(stock_list):
    """批量回测"""
    results = []
    for i, stock in enumerate(stock_list[:100]):
        print(f"[{i+1}/100] {stock}")
        bt = backtest_stock(stock, count=500)
        if bt is not None:
            entries = bt['entries'].shift(1).fillna(False)
            exits = bt['exits'].shift(1).fillna(False)

            # 计算收益
            data = bt['data']
            prices = data['Open']
            trades = []

            in_position = False
            entry_price = 0
            for j in range(1, len(prices)):
                if entries.iloc[j] and not in_position:
                    in_position = True
                    entry_price = prices.iloc[j]
                elif exits.iloc[j] and in_position:
                    ret = (prices.iloc[j] - entry_price) / entry_price
                    trades.append(ret)
                    in_position = False

            if trades:
                total_ret = np.prod([1+t for t in trades]) - 1
                win_rate = sum([t>0 for t in trades]) / len(trades)
                results.append({
                    'stock': stock,
                    'trades': len(trades),
                    'win_rate': win_rate,
                    'total_return': total_ret,
                    'avg_win': np.mean([t for t in trades if t>0]) if trades else 0,
                    'avg_loss': np.mean([t for t in trades if t<0]) if trades else 0
                })

    return results

if __name__ == '__main__':
    print("获取股票列表...")
    stocks = get_stock_list()
    print(f"共 {len(stocks)} 只股票")

    print("开始回测...")
    results = run_backtest(stocks)

    if results:
        df = pd.DataFrame(results)
        print("\n=== 回测结果 ===")
        print(f"股票数: {len(results)}")
        print(f"总交易次数: {df['trades'].sum()}")
        print(f"平均胜率: {df['win_rate'].mean():.2%}")
        print(f"平均收益: {df['total_return'].mean():.2%}")
        print(f"正收益股: {sum(df['total_return']>0)}/{len(df)}")
        print("\nTop 10:")
        print(df.nlargest(10, 'total_return')[['stock','trades','win_rate','total_return']])