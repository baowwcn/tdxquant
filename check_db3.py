import sqlite3

conn = sqlite3.connect("C:/new_tdx64/PYPlugins/user/a_share_monthly.db")
cur = conn.cursor()
cur.execute(
    "SELECT COUNT(*), MIN(date), MAX(date) FROM stock_data WHERE code='000001.SZ'"
)
print("000001.SZ:", cur.fetchone())
cur.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM stock_data")
print("Total:", cur.fetchone())
cur.execute("SELECT code FROM stock_data LIMIT 10")
print("Sample codes:", [r[0] for r in cur.fetchall()])
conn.close()
