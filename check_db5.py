import sqlite3

conn = sqlite3.connect("C:/new_tdx64/PYPlugins/user/a_share_full.db")
cur = conn.cursor()
cur.execute(
    "SELECT COUNT(*), MIN(date), MAX(date) FROM stock_data WHERE code='000001.SZ'"
)
print("000001.SZ daily data:", cur.fetchone())
cur.execute(
    "SELECT date FROM stock_data WHERE code='000001.SZ' ORDER BY date DESC LIMIT 5"
)
print("Latest 5 dates:", [r[0] for r in cur.fetchall()])
conn.close()
