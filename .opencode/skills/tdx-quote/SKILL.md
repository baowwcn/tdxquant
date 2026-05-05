---
name: tdx-quote
description: Query stock quote data (K-line, snapshot, real-time quotes) via TdxQuant API
---

# 通达信行情查询 Skill

基于 `tqcenter.py` 获取股票行情数据。

## 初始化

```python
import sys, os
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
tq.initialize('dummy.py')
```

## 常用接口

### 1. 历史K线数据

```python
result = tq.get_market_data(
    field_list=['Close', 'Open', 'High', 'Low', 'Volume', 'Amount'],
    stock_list=['002758.SZ'],  # 股票代码格式: 000001.SZ, 600000.SH
    period='1d',              # 周期: 1m/5m/15m/1h/1d
    count=5                   # 获取最近N条
)
# result 是 dict，key 是字段名，value 是 DataFrame
# DataFrame index 是日期，columns 是股票代码
```

### 2. 实时快照

```python
snapshot = tq.get_market_snapshot('002758.SZ')
# 返回: {'Now': 现价, 'LastClose': 前收, 'Volume': 总手, 'Amount': 总成交额(万元), ...}
```

### 3. 扩展信息

```python
info = tq.get_more_info('002758.SZ', ['ZAF', 'Zsz', 'FCAmo'])
# ZAF: 涨幅%, Zsz: 总市值(亿), FCAmo: 封单额(万, >0涨停, <0跌停)
```

## 示例

### 查询单只股票最近N天数据

```python
import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
tq.initialize('dummy.py')

result = tq.get_market_data(
    ['Close', 'Open', 'High', 'Low', 'Volume', 'Amount'],
    ['002758.SZ'],
    '1d',
    count=5
)
for field, df in result.items():
    print(df)
tq.close()
```

### 批量查询多只股票

```python
stock_list = ['000001.SZ', '600000.SH', '002758.SZ']
result = tq.get_market_data(['Close', 'Volume'], stock_list, '1d', count=10)
print(result['Close'])  # 所有股票的收盘价
```