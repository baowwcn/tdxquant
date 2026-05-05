import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import numpy as np
import pandas as pd

print("Starting...", flush=True)

tq.initialize('d.py')

print("Getting stocks...", flush=True)
stocks = tq.get_stock_list(market='5', list_type=0)[:20] + tq.get_stock_list(market='6', list_type=0)[:20]
print(f"Got {len(stocks)} stocks", flush=True)

results = []

for s in stocks:
    try:
        df = tq.get_market_data(['Close','Open'], [s], '1d', dividend_type='none', count=500)
        if 'Close' not in df or s not in df['Close']:
            continue

        close = df['Close'][s]
        if len(close) < 100:
            continue

        ma = close.rolling(20).mean()
        std = close.rolling(20).std()
        lower = ma - 2 * std

        entry = df['Open'][s] < lower
        exits = df['Open'][s] < lower

        trades = []
        in_pos = False
        entry_price = 0

        for i in range(1, len(close)):
            if entry.iloc[i] and not in_pos:
                in_pos = True
                entry_price = df['Open'][s].iloc[i]
            elif exits.iloc[i] and in_pos:
                ret = (df['Open'][s].iloc[i] - entry_price) / entry_price
                trades.append(ret)
                in_pos = False

        if trades:
            total_ret = np.prod([1 + t for t in trades]) - 1
            win_rate = sum([t > 0 for t in trades]) / len(trades)
            results.append({'stock': s, 'trades': len(trades), 'return': total_ret, 'win_rate': win_rate})
    except Exception as e:
        print(f"Error {s}: {e}", flush=True)
        pass

print(f"Results: {len(results)}", flush=True)

if results:
    df = pd.DataFrame(results)
    print('Stock count:', len(results), flush=True)
    print('Avg return:', df['return'].mean(), flush=True)
    print('Avg win rate:', df['win_rate'].mean(), flush=True)
    print('Profit stocks:', sum(df['return'] > 0), '/', len(df), flush=True)
    print('Top5:', flush=True)
    print(df.nlargest(5, 'return')[['stock', 'trades', 'return', 'win_rate']], flush=True)

tq.close()
print("Done", flush=True)