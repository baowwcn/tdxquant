import sqlite3

conn = sqlite3.connect("C:/new_tdx64/PYPlugins/user/a_share_monthly.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())
cur.execute("PRAGMA table_info(stock_data)")
print("Columns:", cur.fetchall())
cur.execute(
    "SELECT date FROM stock_data WHERE code='000001.SZ' ORDER BY date DESC LIMIT 5"
)
print("Sample dates:", [r[0] for r in cur.fetchall()])
conn.close()
