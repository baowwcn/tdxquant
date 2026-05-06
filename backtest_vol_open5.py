"""
量化回测：开盘5分钟成交量大于昨天开盘5分钟成交量的股票，3天内收益5%以上
"""

import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import numpy as np
import pandas as pd

tq.initialize('dummy.py')

def get_open5min_volumes(stock_code, count=60):
    """
    获取股票的每日开盘5分钟成交量（第一个5分钟bar）
    返回字典：{日期: 成交量}，日期格式YYYY-MM-DD
    """
    try:
        df = tq.get_market_data(['Volume'], [stock_code], '5m', count=count * 5)
        if 'Volume' not in df or stock_code not in df['Volume']:
            return None
        vol = df['Volume'][stock_code]
        
        daily_volumes = {}
        sorted_idx = vol.index.sort_values()
        
        for idx in sorted_idx:
            date_str = str(idx).split()[0]
            if date_str not in daily_volumes:
                daily_volumes[date_str] = float(vol[idx])
        
        return daily_volumes
    except Exception as e:
        return None

def get_daily_close(stock_code, count=200):
    """获取日线收盘数据，返回Series with date string keys"""
    try:
        df = tq.get_market_data(['Close'], [stock_code], '1d', count=count)
        if 'Close' not in df or stock_code not in df['Close']:
            return None
        close = df['Close'][stock_code]
        result = {}
        for d, v in zip(close.index, close.values):
            result[str(d).split()[0]] = v
        return result
    except:
        return None

def get_open_prices(stock_code, count=200):
    """获取日线开盘价数据，返回字典 with date string keys"""
    try:
        df = tq.get_market_data(['Open'], [stock_code], '1d', count=count)
        if 'Open' not in df or stock_code not in df['Open']:
            return None
        open_p = df['Open'][stock_code]
        result = {}
        for d, v in zip(open_p.index, open_p.values):
            result[str(d).split()[0]] = v
        return result
    except:
        return None

def run_backtest(stock_code, open5_volumes, open_prices, close_prices, days=3):
    trades = []   # 存储所有信号
    common_dates = sorted(set(open5_volumes.keys()) & set(open_prices.keys()) & set(close_prices.keys()))
    
    for i in range(1, len(common_dates) - days):
        curr_date = common_dates[i]
        prev_date = common_dates[i-1]
        
        if open5_volumes[curr_date] > open5_volumes[prev_date] * 1.1:   # 1.1倍
            entry_price = open_prices[curr_date]      # 用开盘价买入
            exit_date = common_dates[i+days]
            exit_price = close_prices[exit_date]      # 3天后收盘卖出
            ret = (exit_price - entry_price) / entry_price

            # 只记录收益大于5%的交易
            if ret <= 0.05:
                continue

            trades.append({
                'date': curr_date,
                'ret': ret,
                'entry': entry_price,
                'exit': exit_price
            })
    return trades

def main():
    print("获取股票列表...")
    stocks = tq.get_stock_list(market='0', list_type=0)
    stocks = [s for s in stocks if s.startswith(('0','3','6'))][:50]
    
    all_trades = []
    stock_trades_count = {}
    
    for i, stock in enumerate(stocks):
        print(f"[{i+1}/{len(stocks)}] {stock}")
        
        open5_vol = get_open5min_volumes(stock, count=60)
        open_prices = get_open_prices(stock, count=200)
        close_prices = get_daily_close(stock, count=200)
        
        if open5_vol is None or open_prices is None or close_prices is None:
            continue
        
        if len(open5_vol) < 5:
            continue
        
        trades = run_backtest(stock, open5_vol, open_prices, close_prices)
        if trades:
            all_trades.extend(trades)
            stock_trades_count[stock] = len(trades)
            for t in trades:
                t['stock'] = stock
            print(f"  -> {len(trades)} trades")
    
    print("\n" + "="*50)
    print("=== 回测结果 ===")
    print("="*50)
    
    if all_trades:
        returns = [t['ret'] for t in all_trades]
        print(f"符合条件交易次数: {len(all_trades)}")
        print(f"平均收益率: {np.mean(returns):.2%}")
        print(f"中位收益率: {np.median(returns):.2%}")
        print(f"最大收益率: {max(returns):.2%}")
        print(f"最小收益率: {min(returns):.2%}")
        
        df = pd.DataFrame(all_trades)
        print("\n所有交易记录:")
        print(df.sort_values('ret', ascending=False))
        
        print("\n按股票统计:")
        for stock, count in stock_trades_count.items():
            stock_returns = [t['ret'] for t in all_trades if t.get('stock') == stock]
            print(f"  {stock}: {count} trades, avg return: {np.mean(stock_returns):.2%}")
    else:
        print("没有符合条件的交易")
        
        print("\n调试: 分析开盘量分布...")
        for stock in stocks[:10]:
            open5_vol = get_open5min_volumes(stock, count=60)
            if open5_vol and len(open5_vol) >= 2:
                vals = sorted(open5_vol.values())
                up_ratio = sum(1 for i in range(1, len(vals)) if vals[i] > vals[i-1] * 1.1)
                print(f"  {stock}: {len(open5_vol)} days, {up_ratio} up-days (>1.1x)")

if __name__ == '__main__':
    main()