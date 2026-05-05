import sys
import pandas as pd
import numpy as np
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
tq.initialize('dummy.py')

stocks = tq.get_stock_list_in_sector('ZT', block_type=1)
print(f'Total stocks: {len(stocks)}')

result = tq.get_market_data(
    ['Close', 'Open', 'High', 'Low', 'Volume', 'Amount'],
    stocks,
    '1d',
    count=150
)

tq.close()

stats = []
for code in stocks:
    try:
        close = result['Close'][code].dropna()
        vol = result['Volume'][code].dropna()

        if len(close) < 120:
            continue

        ma5 = close.rolling(5).mean().iloc[-1]
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1]
        ma120 = close.rolling(120).mean().iloc[-1]

        current_price = close.iloc[-1]

        vol_recent5 = vol.iloc[-5:].mean()
        vol_prev20 = vol.iloc[-25:-5].mean() if len(vol) > 25 else vol.mean()
        vol_ratio = vol_recent5 / vol_prev20 if vol_prev20 > 0 else np.nan

        short_term_good = (ma5 > ma10 > ma20)
        medium_term_good = (ma20 > ma60)
        long_term_good = (ma60 > ma120)

        above_ma5 = current_price > ma5
        above_ma10 = current_price > ma10
        above_ma20 = current_price > ma20
        above_ma60 = current_price > ma60
        above_ma120 = current_price > ma120

        stats.append({
            'code': code,
            'price': round(current_price, 2),
            'ma5': round(ma5, 2),
            'ma10': round(ma10, 2),
            'ma20': round(ma20, 2),
            'ma60': round(ma60, 2),
            'ma120': round(ma120, 2),
            'short_term_good': short_term_good,
            'medium_term_good': medium_term_good,
            'long_term_good': long_term_good,
            'above_ma5': above_ma5,
            'above_ma10': above_ma10,
            'above_ma20': above_ma20,
            'above_ma60': above_ma60,
            'above_ma120': above_ma120,
            'vol_ratio': round(vol_ratio, 2) if not np.isnan(vol_ratio) else np.nan
        })
    except Exception as e:
        print(f'Error processing {code}: {e}')

df = pd.DataFrame(stats)
print('\n=== Summary ===')
print(f'Short-term bullish (MA5>MA10>MA20): {df["short_term_good"].sum()} / {len(df)} ({df["short_term_good"].mean()*100:.1f}%)')
print(f'Medium-term bullish (MA20>MA60): {df["medium_term_good"].sum()} / {len(df)} ({df["medium_term_good"].mean()*100:.1f}%)')
print(f'Long-term bullish (MA60>MA120): {df["long_term_good"].sum()} / {len(df)} ({df["long_term_good"].mean()*100:.1f}%)')
print(f'Price above MA5: {df["above_ma5"].sum()} / {len(df)} ({df["above_ma5"].mean()*100:.1f}%)')
print(f'Price above MA10: {df["above_ma10"].sum()} / {len(df)} ({df["above_ma10"].mean()*100:.1f}%)')
print(f'Price above MA20: {df["above_ma20"].sum()} / {len(df)} ({df["above_ma20"].mean()*100:.1f}%)')
print(f'Price above MA60: {df["above_ma60"].sum()} / {len(df)} ({df["above_ma60"].mean()*100:.1f}%)')
print(f'Price above MA120: {df["above_ma120"].sum()} / {len(df)} ({df["above_ma120"].mean()*100:.1f}%)')
print(f'Volume ratio (recent5/prev20): median={df["vol_ratio"].median():.2f}, mean={df["vol_ratio"].mean():.2f}')

print('\n=== Stock Details ===')
print(df[['code', 'price', 'ma5', 'ma10', 'ma20', 'ma60', 'ma120', 'vol_ratio']].to_string(index=False))