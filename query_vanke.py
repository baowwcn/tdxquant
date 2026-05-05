import sqlite3

conn = sqlite3.connect("a_share_full.db")
cur = conn.cursor()
cur.execute(
    "SELECT date, open, high, low, close, volume FROM stock_data WHERE code='000002.SZ' AND date >= '2026-04-07' ORDER BY date"
)
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
