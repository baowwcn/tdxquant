A股股票数据库

## 概述
本数据库包含中国A股市场所有股票的历史日线数据，存储在SQLite数据库中。

## 数据库信息

### 全量历史数据库 (a_share_full.db)
- **文件名**: `a_share_full.db`
- **股票数量**: 5500+只
- **总记录数**: 2300万+条
- **时间范围**: 1990年至今
- **数据频率**: 日线数据
- **数据来源**: 本地通达信软件数据文件

### 月度数据库 (a_share_monthly.db)
- **文件名**: `a_share_monthly.db`
- **股票数量**: 2300只
- **总记录数**: 5万+条
- **时间范围**: 最近一个月
- **数据频率**: 日线数据
- **数据来源**: TdxQuant API

## 表结构
### stock_data 表
| 字段 | 类型 | 说明 |
|------|------|------|
| code | TEXT | 股票代码（如 000001.SZ, 600000.SH） |
| date | TEXT | 交易日期（YYYY-MM-DD） |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| volume | REAL | 成交量（手） |
| amount | REAL | 成交额（元） |

## 使用方法

### 1. 基本查询
```python
from query_a_share_db import query_stock_data, get_stock_summary

# 获取数据库统计信息
summary = get_stock_summary('a_share_full.db')
print(f"总股票数: {summary['total_stocks']}")

# 查询特定股票数据
df = query_stock_data(code='000002.SZ', db_path='a_share_full.db', limit=10)
print(df)
```

### 2. 高级查询示例
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('a_share_full.db')

# 查询特定日期范围
query = """
SELECT * FROM stock_data
WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
  AND code = '000002.SZ'
ORDER BY date
"""
df = pd.read_sql_query(query, conn)

# 计算涨跌幅
df['pct_change'] = df['close'].pct_change()

# 查找成交量最大的股票
query = """
SELECT code, SUM(volume) as total_volume
FROM stock_data
GROUP BY code
ORDER BY total_volume DESC
LIMIT 10
"""
top_volume = pd.read_sql_query(query, conn)

conn.close()
```

### 3. 数据分析示例
```python
# 计算每只股票的平均收盘价
query = """
SELECT code, AVG(close) as avg_close, COUNT(*) as days
FROM stock_data
GROUP BY code
HAVING days >= 20
ORDER BY avg_close DESC
LIMIT 10
"""
high_price_stocks = pd.read_sql_query(query, conn)
```

## 文件说明
- `store_a_share_data.py`: 从TdxQuant API获取月度数据
- `query_a_share_db.py`: 数据库查询工具脚本
- `import_tdx_vipdoc_to_sqlite.py`: 从本地通达信数据文件导入全量历史数据
- `fix_a_share_full_code_suffix.py`: 修复股票代码后缀的工具脚本
- `a_share_full.db`: 全量历史数据SQLite数据库
- `a_share_monthly.db`: 月度数据SQLite数据库

## 数据更新方法

### 1. 追加新数据
当通达信软件有新数据时，可以追加更新：

```bash
# 追加最近一个月的数据
python import_tdx_vipdoc_to_sqlite.py --last-month

# 追加最近一年的数据
python import_tdx_vipdoc_to_sqlite.py --last-year

# 追加最近3年的数据
python import_tdx_vipdoc_to_sqlite.py --last-3years
```

如果数据库文件在网络共享上：

```bash
python import_tdx_vipdoc_to_sqlite.py --db "\\192.168.1.108\m600\stock\data\a_share_full.db"
```

如果通达信安装目录不是默认 `C:\new_tdx64`：

```bash
python import_tdx_vipdoc_to_sqlite.py --vipdoc-root "D:\tdx" --db "\\192.168.1.108\m600\stock\data\a_share_full.db"
```

### 2. 固定时间段覆盖更新
如果需要更新特定时间段的数据，可以使用时间范围参数：

```bash
# 更新2024年的数据
python import_tdx_vipdoc_to_sqlite.py --start-date 2024-01-01 --end-date 2024-12-31

# 只保留2020年至今的数据，删除更早的数据
python import_tdx_vipdoc_to_sqlite.py --start-date 2020-01-01 --keep-only-range


# 更新最近30天的数据
python import_tdx_vipdoc_to_sqlite.py --start-date 2024-03-01 --end-date 2024-04-01
```

### 3. 完整重新导入
如果需要重新导入所有数据：

```bash
# 重新导入所有历史数据
python import_tdx_vipdoc_to_sqlite.py
```

### 4. 月度数据更新
更新月度数据库（从API获取）：

```bash
python store_a_share_data.py
```

## 注意事项
- 全量历史数据来自本地通达信软件的vipdoc目录
- 所有价格单位为人民币元
- 成交量单位为手（100股）
- 数据库使用股票代码和日期作为联合主键，避免重复数据
- 上海股票代码以.SH结尾，深圳股票以.SZ结尾
- 建议定期备份数据库文件

## 常见问题

### Q: 如何查看数据库中的数据范围？
```python
import sqlite3
conn = sqlite3.connect('a_share_full.db')
result = conn.execute('SELECT MIN(date), MAX(date), COUNT(*) FROM stock_data').fetchone()
print(f"日期范围: {result[0]} 到 {result[1]}, 总记录数: {result[2]}")
conn.close()
```

### Q: 如何查看特定股票的数据？
```python
from query_a_share_db import query_stock_data
df = query_stock_data('000002.SZ', 'a_share_full.db')
print(df.head())
```

### Q: 本次查询中常用的 SQL 查询方法是什么？
以下是本轮查询中使用的几种命令，直接在命令行执行即可查看数据：

```bash
# 查询万科 1992 年 3 月的数据
python -c "import sqlite3, pandas as pd; conn = sqlite3.connect('a_share_full.db'); query = 'SELECT * FROM stock_data WHERE code = \'000002.SZ\' AND date BETWEEN \'1992-03-01\' AND \'1992-03-31\' ORDER BY date'; df = pd.read_sql_query(query, conn); print(df.to_string(index=False)); conn.close()"
```

```bash
# 查询万科 1991 年的数据记录数和日期范围
python -c "import sqlite3; conn = sqlite3.connect('a_share_full.db'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM stock_data WHERE code = \'000002.SZ\' AND date LIKE \'1991%\''); print('万科1991年记录数:', cur.fetchone()[0]); cur.execute('SELECT MIN(date), MAX(date) FROM stock_data WHERE code = \'000002.SZ\''); print('万科数据日期范围:', cur.fetchone()); conn.close()"
```

```bash
# 查询数据库最新日期
python -c "import sqlite3; conn = sqlite3.connect('a_share_full.db'); cur = conn.cursor(); cur.execute('SELECT MAX(date) FROM stock_data'); latest_date = cur.fetchone()[0]; print('数据库最新日期:', latest_date); conn.close()"
```

### Q: 数据更新后如何验证？
运行查询脚本检查数据范围和记录数：
```bash
python query_a_share_db.py --db a_share_full.db
```
1. 保持通达信数据更新到本地 `C:\new_tdx64\vipdoc\sh\lday\` 和 `C:\new_tdx64\vipdoc\sz\lday\`。
2. 运行以下命令：
```powershell
c:/new_tdx64/PYPlugins/user/.venv-1/Scripts/python.exe import_tdx_vipdoc_to_sqlite.py
```
3. 脚本会扫描所有 `.day` 文件，并将数据追加到本地 SQLite 数据库 `a_share_full.db` 中。

### 增量更新说明
- `import_tdx_vipdoc_to_sqlite.py` 使用 `INSERT OR REPLACE`，同一支股票同一交易日期的记录不会重复插入。
- 如果本地数据文件更新了，直接重新运行脚本即可追加新日期的数据。
- 如果你只想使用当前的 `a_share_monthly.db`，也可以继续运行 `store_a_share_data.py` 来更新近一个月的数据。