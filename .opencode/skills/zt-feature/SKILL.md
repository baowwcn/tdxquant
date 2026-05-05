---
name: zt-feature
description: Analyze limit-up (涨停) stock patterns: moving averages, volume, and common characteristics
---

# 涨停特征分析 Skill

分析涨停板块股票的均线形态和成交量特征。

## 初始化

```python
import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
tq.initialize('dummy.py')
```

## 分析函数

```python
def analyze_zt_features(stocks, count=150):
    """
    分析涨停股票的均线和成交量特征

    Args:
        stocks: list of stock codes, e.g. ['002758.SZ', '600000.SH']
        count: K线数量，默认150天

    Returns:
        DataFrame with columns:
        - code, price, ma5, ma10, ma20, ma60, ma120
        - short_term_good: MA5 > MA10 > MA20
        - medium_term_good: MA20 > MA60
        - long_term_good: MA60 > MA120
        - above_ma5/10/20/60/120: price above MA
        - vol_ratio: recent5_vol / prev20_vol
    """
    result = tq.get_market_data(
        ['Close', 'Volume'],
        stocks,
        '1d',
        count=count
    )

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

            stats.append({
                'code': code,
                'price': round(current_price, 2),
                'ma5': round(ma5, 2),
                'ma10': round(ma10, 2),
                'ma20': round(ma20, 2),
                'ma60': round(ma60, 2),
                'ma120': round(ma120, 2),
                'short_term_good': ma5 > ma10 > ma20,
                'medium_term_good': ma20 > ma60,
                'long_term_good': ma60 > ma120,
                'above_ma5': current_price > ma5,
                'above_ma10': current_price > ma10,
                'above_ma20': current_price > ma20,
                'above_ma60': current_price > ma60,
                'above_ma120': current_price > ma120,
                'vol_ratio': round(vol_ratio, 2) if not np.isnan(vol_ratio) else np.nan
            })
        except Exception as e:
            print(f'Error: {code}: {e}')

    return pd.DataFrame(stats)
```

## 使用示例

```python
import sys
import pandas as pd
import numpy as np
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
tq.initialize('dummy.py')

# 获取涨停板块股票
stocks = tq.get_stock_list_in_sector('ZT', block_type=1)
print(f'Total: {len(stocks)}')

# 分析
df = analyze_zt_features(stocks)

# 汇总统计
print(f'Short-term bullish: {df["short_term_good"].sum()}/{len(df)} ({df["short_term_good"].mean()*100:.1f}%)')
print(f'Medium-term bullish: {df["medium_term_good"].sum()}/{len(df)} ({df["medium_term_good"].mean()*100:.1f}%)')
print(f'Long-term bullish: {df["long_term_good"].sum()}/{len(df)} ({df["long_term_good"].mean()*100:.1f}%)')
print(f'Volume ratio median: {df["vol_ratio"].median():.2f}')

tq.close()
```

## 涨停共性特征

| 特征 | 达标比例 | 说明 |
|------|----------|------|
| 短期多头 (MA5>MA10>MA20) | ~77% | 最强信号，均线呈上升趋势 |
| 价格 > MA5 | ~97% | 处于强势上涨中 |
| 价格 > MA20 | ~94% | 站上中期均线 |
| 量比 > 1.0 | >75% | 成交量放大 |
| 中期多头 (MA20>MA60) | ~50% | 分化，部分刚突破 |

## 典型涨停形态

1. **短期突破型**: MA5 > MA10 > MA20 + 价格 > MA5 + 量比 > 1.5
2. **中期启动型**: MA20 > MA60 + 价格 > MA20 + 量比 > 1.2
3. **长期反转型**: MA60 > MA120 + 价格 > MA60 + 量比 > 1.0