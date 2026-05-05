import sqlite3

conn = sqlite3.connect("a_share_full.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print([t[0] for t in cur.fetchall()])
conn.close()
