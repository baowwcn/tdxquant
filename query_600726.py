import sqlite3
from pathlib import Path
import csv
DB = Path('E:/new_tdx64/PYPlugins/user/a_share_full.db')
if not DB.exists():
    print('DB not found:', DB)
    raise SystemExit(1)
conn = sqlite3.connect(str(DB))
cur = conn.cursor()
code = '600726.SH'
cur.execute("SELECT date, open, high, low, close, volume, amount FROM stock_data WHERE code=? ORDER BY date DESC LIMIT 60", (code,))
rows = cur.fetchall()
conn.close()
writer = csv.writer(open('query_600726.csv','w', newline=''))
writer.writerow(['date','open','high','low','close','volume','amount'])
writer.writerows(rows)
# also print to stdout
import sys
w = csv.writer(sys.stdout)
w.writerow(['date','open','high','low','close','volume','amount'])
w.writerows(rows)
