import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import pandas as pd
import numpy as np

tq.initialize('dummy.py')

stocks = ['001211.SZ']
result = tq.get_market_data(['Close'], stocks, '1d', count=250)

close = result['Close']['001211.SZ'].dropna()

ma60 = close.rolling(60).mean()
ma120 = close.rolling(120).mean()

recent = close.tail(120)

print('='*60)
print('股票001211 近半年均线特征')
print('='*60)

print(f'\n当前价格: {close.iloc[-1]:.2f}')
print(f'当前MA60: {ma60.iloc[-1]:.2f}')
print(f'当前MA120: {ma120.iloc[-1]:.2f}')

print(f'\n=== 均线位置关系 ===')
print(f'MA60 > MA120: {ma60.iloc[-1] > ma120.iloc[-1]} (长期均线多头)')
print(f'价格 > MA60: {close.iloc[-1] > ma60.iloc[-1]}')
print(f'价格 > MA120: {close.iloc[-1] > ma120.iloc[-1]}')

print(f'\n=== 近60日均线变化 ===')
ma60_60d_ago = ma60.iloc[-61]
ma60_30d_ago = ma60.iloc[-31]
ma60_now = ma60.iloc[-1]
print(f'60日前MA60: {ma60_60d_ago:.2f}')
print(f'30日前MA60: {ma60_30d_ago:.2f}')
print(f'当前MA60: {ma60_now:.2f}')
print(f'60日变化: {ma60_now - ma60_60d_ago:+.2f} ({((ma60_now/ma60_60d_ago)-1)*100:+.1f}%)')

print(f'\n=== 近120日均线变化 ===')
ma120_120d_ago = ma120.iloc[-121]
ma120_60d_ago = ma60.iloc[-61]
ma120_now = ma120.iloc[-1]
print(f'120日前MA120: {ma120_120d_ago:.2f}')
print(f'60日前MA120: {ma120_60d_ago:.2f}')
print(f'当前MA120: {ma120_now:.2f}')
print(f'120日变化: {ma120_now - ma120_120d_ago:+.2f} ({((ma120_now/ma120_120d_ago)-1)*100:+.1f}%)')

print(f'\n=== 黄金交叉/死叉 ===')
for i in range(-60, 0):
    prev_diff = ma60.iloc[i-1] - ma120.iloc[i-1]
    curr_diff = ma60.iloc[i] - ma120.iloc[i]
    if prev_diff < 0 and curr_diff > 0:
        print(f'黄金交叉: {close.index[i].strftime("%Y-%m-%d")} (MA60上穿MA120)')
    elif prev_diff > 0 and curr_diff < 0:
        print(f'死叉: {close.index[i].strftime("%Y-%m-%d")} (MA60下穿MA120)')

crossover_count = 0
for i in range(-120, -60):
    if i == -120:
        continue
    prev_diff = ma60.iloc[i-1] - ma120.iloc[i-1]
    curr_diff = ma60.iloc[i] - ma120.iloc[i]
    if prev_diff < 0 and curr_diff > 0:
        crossover_count += 1

print(f'\n近半年黄金交叉次数: {crossover_count}')

tq.close()