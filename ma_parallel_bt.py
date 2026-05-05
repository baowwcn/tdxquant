"""
均线平行向上选股公式回测
公式逻辑:
- MA60斜率与MA120斜率接近(差值<=0.02)
- MA60斜率>MA120斜率
- 两斜率都为正(多头排列)
"""

import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import numpy as np
import pandas as pd

tq.initialize('d.py')

def linear_slope(series, period):
    """计算线性回归斜率"""
    x = np.arange(period)
    y = series.values
    if len(y) < period:
        return np.nan
    y = y[-period:]
    x_mean = x.mean()
    y_mean = y.mean()
    slope = np.sum((x - x_mean) * (y - y_mean)) / (np.sum((x - x_mean)**2) + 1e-9)
    return slope

def backtest_ma_parallel():
    stocks = tq.get_stock_list(market='5', list_type=0)[:100]
    results = []

    for s in stocks:
        try:
            df = tq.get_market_data(['Close','Open'], [s], '1d', dividend_type='none', count=250)
            if 'Close' not in df or s not in df['Close']:
                continue

            close = df['Close'][s]
            if len(close) < 150:
                continue

            ma60 = close.rolling(60).mean()
            ma120 = close.rolling(120).mean()

            k60 = linear_slope(ma60, 120)
            k120 = linear_slope(ma120, 120)

            if np.isnan(k60) or np.isnan(k120):
                continue

            # 公式条件: |K60-K120|<=0.02 AND K60>K120 AND K60*K120>=0
            cond1 = abs(k60 - k120) <= 0.02
            cond2 = k60 > k120
            cond3 = k60 * k120 >= 0

            signal = cond1 and cond2 and cond3

            if signal:
                # 入场: 明日开盘买入
                # 出场: 10日后卖出(持有N天)
                entry_price = df['Open'][s].iloc[-1]
                exit_price = df['Close'][s].iloc[-1]

                ret = (exit_price - entry_price) / entry_price

                results.append({
                    'stock': s,
                    'k60': k60,
                    'k120': k120,
                    'diff': k60 - k120,
                    'return': ret
                })
        except Exception as e:
            pass

    print("=== 均线平行向上选股回测 ===")
    print(f"选出股票数: {len(results)}")

    if results:
        df = pd.DataFrame(results)
        print(f"平均收益: {df['return'].mean():.2%}")
        print(f"正收益: {sum(df['return']>0)}/{len(df)}")
        print("\n选出股票:")
        print(df[['stock','k60','k120','diff','return']].sort_values('return', ascending=False).head(20))

if __name__ == '__main__':
    backtest_ma_parallel()
    tq.close()