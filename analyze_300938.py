import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq

tq.initialize('dummy.py')

stocks = ['300938.SZ']
result = tq.get_market_data(['Close'], stocks, '1d', count=250)

close = result['Close']['300938.SZ'].dropna()

ma60 = close.rolling(60).mean()
ma120 = close.rolling(120).mean()

print('='*60)
print('股票300938 均线特征')
print('='*60)

print(f'\n当前价格: {close.iloc[-1]:.2f}')
print(f'当前MA60: {ma60.iloc[-1]:.2f}')
print(f'当前MA120: {ma120.iloc[-1]:.2f}')

print(f'\n=== 均线位置关系 ===')
print(f'MA60 > MA120: {ma60.iloc[-1] > ma120.iloc[-1]}')

print(f'\n=== 近半年MA60变化 ===')
ma60_60d_ago = ma60.iloc[-61]
ma60_now = ma60.iloc[-1]
print(f'60日前: {ma60_60d_ago:.2f} → 当前: {ma60_now:.2f} ({ma60_now-ma60_60d_ago:+.2f}, {((ma60_now/ma60_60d_ago)-1)*100:+.1f}%)')

print(f'\n=== 近半年MA120变化 ===')
ma120_120d_ago = ma120.iloc[-121]
ma120_now = ma120.iloc[-1]
print(f'120日前: {ma120_120d_ago:.2f} → 当前: {ma120_now:.2f} ({ma120_now-ma120_120d_ago:+.2f}, {((ma120_now/ma120_120d_ago)-1)*100:+.1f}%)')

print(f'\n=== 两条线上升幅度对比 ===')
ma60_rise = (ma60_now/ma60_60d_ago - 1) * 100
ma120_rise = (ma120_now/ma120_120d_ago - 1) * 100
print(f'MA60近半年涨幅: {ma60_rise:+.1f}%')
print(f'MA120近半年涨幅: {ma120_rise:+.1f}%')
print(f'差异: {abs(ma60_rise - ma120_rise):.1f}% (近似平行={abs(ma60_rise - ma120_rise) < 2})')

tq.close()