import sqlite3

conn = sqlite3.connect('a_share_full.db')
cur = conn.cursor()

# 查看所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("数据库中的所有表:")
for table in tables:
    print(f"  {table[0]}")

# 查看 stock_data 表的一些样本数据
print("\nstock_data 表样本数据:")
cur.execute("SELECT * FROM stock_data LIMIT 5")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()
