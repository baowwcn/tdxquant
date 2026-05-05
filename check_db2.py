import sqlite3

conn = sqlite3.connect("C:/new_tdx64/PYPlugins/user/data/ashare_daily.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)
if tables:
    for t in tables:
        cur.execute(f"PRAGMA table_info({t[0]})")
        print(f"{t[0]} columns:", cur.fetchall())
conn.close()
