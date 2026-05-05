import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'a_share_full.db'
VIPDOC_DIR = Path(r'C:\new_tdx64\vipdoc')

if not DB_PATH.exists():
    raise FileNotFoundError(f'Database not found: {DB_PATH}')

sh_dir = VIPDOC_DIR / 'sh' / 'lday'
sz_dir = VIPDOC_DIR / 'sz' / 'lday'
if not sh_dir.exists() or not sz_dir.exists():
    raise FileNotFoundError('Cannot find sh/lday or sz/lday under vipdoc')

sh_codes = sorted(p.stem[2:] for p in sh_dir.glob('sh*.day'))
sz_codes = sorted(p.stem[2:] for p in sz_dir.glob('sz*.day'))
print(f'Fixing codes for {len(sh_codes)} SH files and {len(sz_codes)} SZ files')

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('PRAGMA journal_mode=WAL')
cur.execute('PRAGMA synchronous=NORMAL')
cur.execute('PRAGMA cache_size=100000')
conn.commit()

try:
    cur.execute('BEGIN TRANSACTION')
    for code in sh_codes:
        cur.execute('UPDATE stock_data SET code = ? WHERE code = ?', (code + '.SH', code))
    for code in sz_codes:
        cur.execute('UPDATE stock_data SET code = ? WHERE code = ?', (code + '.SZ', code))
    conn.commit()
finally:
    conn.close()

print('Code suffix fix complete.')
