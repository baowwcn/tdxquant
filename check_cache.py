import sqlite3

conn = sqlite3.connect("C:/new_tdx64/T0002/CacheData.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)
if tables:
    for t in tables:
        cur.execute(f"PRAGMA table_info({t[0]})")
        print(f"{t[0]} columns:", [c[1] for c in cur.fetchall()])
        try:
            cur.execute(
                f"SELECT COUNT(*), MIN(date), MAX(date) FROM {t[0]} WHERE code='000001.SZ'"
            )
            print(f"  000001.SZ:", cur.fetchone())
        except:
            pass
conn.close()
