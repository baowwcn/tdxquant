import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 连接数据库
conn = sqlite3.connect('a_share_full.db')
cur = conn.cursor()

# 查找同济科技的股票代码
print("正在查找同济科技的股票代码...")
cur.execute("SELECT code, name FROM stock_data WHERE name LIKE '%同济科技%' GROUP BY code")
rows = cur.fetchall()
print(f"找到 {len(rows)} 只相关股票:")
for code, name in rows:
    print(f"  {code} - {name}")

# 计算一个月前的日期
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
print(f"\n查询时间范围: {start_date} 到 {end_date}")

# 查询每只股票近一个月的数据
for code, name in rows:
    print(f"\n{code} - {name} 近一个月数据:")
    query = """
    SELECT date, open, high, low, close, volume, amount
    FROM stock_data
    WHERE code = ? AND date BETWEEN ? AND ?
    ORDER BY date DESC
    """
    df = pd.read_sql_query(query, conn, params=(code, start_date, end_date))

    if df.empty:
        print("  近一个月无数据")
    else:
        print(f"  共 {len(df)} 个交易日:")
        # 计算涨跌幅
        df['涨跌幅'] = df['close'].pct_change() * 100
        print(df.to_string(index=False))

conn.close()
