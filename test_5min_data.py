import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq

tq.initialize('dummy.py')

# Test one stock with debug
stock = '002758.SZ'
print(f"Testing {stock}")

# Get 5min data
df = tq.get_market_data(['Volume'], [stock], '5m', count=200)
vol = df['Volume'][stock]

# First 5min each day
daily_vol = {}
sorted_idx = vol.index.sort_values()
for idx in sorted_idx:
    date_str = str(idx).split()[0]
    if date_str not in daily_vol:
        daily_vol[date_str] = vol[idx]

print(f"Daily 5min volumes: {len(daily_vol)} days")
for d, v in list(daily_vol.items())[:5]:
    print(f"  {d}: {v}")

# Get daily close
df_daily = tq.get_market_data(['Close'], [stock], '1d', count=100)
close = df_daily['Close'][stock]

print(f"\nDaily close: {len(close)} days")
for d, c in zip(close.index[:5], close[:5]):
    print(f"  {d}: {c}")

# Check if dates align
vol_dates = set(daily_vol.keys())
close_dates = set(str(d).split()[0] for d in close.index)

print(f"\nVol dates count: {len(vol_dates)}")
print(f"Close dates count: {len(close_dates)}")
print(f"Common dates: {len(vol_dates & close_dates)}")

tq.close()