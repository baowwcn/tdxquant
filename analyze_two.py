import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import pandas as pd
import numpy as np

tq.initialize('dummy.py')

stocks = ['300938.SZ', '001211.SZ']
result = tq.get_market_data(['Close'], stocks, '1d', count=250)

print('='*70)
print('近期两条线差距变化 (近60日)')
print('='*70)

for code in stocks:
    close = result['Close'][code].dropna()
    ma60 = close.rolling(60).mean()
    ma120 = close.rolling(120).mean()
    
    gap = ma60 - ma120
    
    print(f'\n=== {code} ===')
    print(f'当前MA60-MA120差值: {gap.iloc[-1]:.2f}')
    
    for i in [-5, -10, -20, -30]:
        print(f'{abs(i)}日前差值: {gap.iloc[i]:.2f}')
    
    gap_std = gap.iloc[-60:].std()
    gap_mean = gap.iloc[-60:].mean()
    print(f'近60日差值标准差: {gap_std:.2f}')
    print(f'差值波动系数: {gap_std/gap_mean*100:.1f}%')

tq.close()