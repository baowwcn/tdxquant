import sqlite3
import pandas as pd
from datetime import datetime, timedelta

conn = sqlite3.connect('a_share_full.db')
cur = conn.cursor()

# 同济科技股票代码
code = '600846.SH'
stock_name = '同济科技'

# 计算查询时间范围（近一个月）
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

print(f"查询 {stock_name}({code}) 近一个月数据")
print(f"时间范围: {start_date} 到 {end_date}")
print("=" * 80)

# 查询数据
query = """
SELECT date, open, high, low, close, volume, amount
FROM stock_data
WHERE code = ? AND date BETWEEN ? AND ?
ORDER BY date
"""
df = pd.read_sql_query(query, conn, params=(code, start_date, end_date))

if df.empty:
    print("近一个月无交易数据")
else:
    print(f"共 {len(df)} 个交易日\n")

    # 计算每日涨跌幅
    df['涨跌幅(%)'] = df['close'].pct_change() * 100
    df['涨跌幅(%)'] = df['涨跌幅(%)'].round(2)

    # 计算累计涨跌幅
    if len(df) > 0:
        first_close = df['close'].iloc[0]
        last_close = df['close'].iloc[-1]
        total_change = ((last_close - first_close) / first_close) * 100
        print(f"月初收盘价: {first_close:.2f}元")
        print(f"最新收盘价: {last_close:.2f}元")
        print(f"月内累计涨幅: {total_change:.2f}%")
        print()

    # 打印详细数据
    print("日期       开盘   最高   最低   收盘   成交量(手)    成交额(元)    涨跌幅(%)")
    print("-" * 80)
    for _, row in df.iterrows():
        print(f"{row['date']}  {row['open']:6.2f}  {row['high']:6.2f}  {row['low']:6.2f}  {row['close']:6.2f}  {int(row['volume']):10d}  {row['amount']:12.2f}  {row['涨跌幅(%)']:7.2f}")

conn.close()
print("\n查询完成")
