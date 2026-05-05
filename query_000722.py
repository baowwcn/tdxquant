import sqlite3

conn = sqlite3.connect('a_share_monthly.db')
cur = conn.cursor()

# 查询000722最近5天数据
cur.execute("""
    SELECT code, date, open, high, low, close, volume 
    FROM stock_data 
    WHERE code = '000722.SZ' 
    ORDER BY date DESC 
    LIMIT 5
""")

rows = cur.fetchall()
print("=== 000722 (湖南发展) 最近5天行情 ===\n")
print(f"{'日期':<12} {'开盘':>8} {'最高':>8} {'最低':>8} {'收盘':>8} {'成交量':>12}")
print("-" * 60)
for r in rows:
    code, date, open, high, low, close, volume = r
    print(f"{date:<12} {open:>8.2f} {high:>8.2f} {low:>8.2f} {close:>8.2f} {volume:>12.0f}")

conn.close()