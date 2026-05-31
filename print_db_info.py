import sqlite3
from pathlib import Path
DB = Path('E:/new_tdx64/PYPlugins/user/a_share_full.db')
if not DB.exists():
    print('DB not found:', DB)
    raise SystemExit(1)
conn = sqlite3.connect(str(DB))
cur = conn.cursor()
cur.execute('SELECT MIN(date), MAX(date), COUNT(*) FROM stock_data')
min_date, max_date, total = cur.fetchone()
cur.execute('SELECT COUNT(DISTINCT code) FROM stock_data')
distinct_codes = cur.fetchone()[0]
conn.close()
print(f'date_range: {min_date} -> {max_date}')
print(f'total_records: {total}')
print(f'distinct_codes: {distinct_codes}')
