"""
Migrate `stock_data` from SQLite to Postgres in chunks.
Usage:
  python sqlite_to_postgres.py --sqlite E:\new_tdx64\PYPlugins\user\a_share_full.db --pg postgresql://user:pass@localhost:5432/a_share --chunksize 10000
"""
import argparse
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS stock_data (
    code TEXT,
    date TEXT,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    amount DOUBLE PRECISION
);
'''

INSERT_SQL = "INSERT INTO stock_data (code,date,open,high,low,close,volume,amount) VALUES %s"

parser = argparse.ArgumentParser()
parser.add_argument('--sqlite', required=True)
parser.add_argument('--pg', required=True, help='Postgres connection string, e.g. postgresql://user:pass@host:5432/db')
parser.add_argument('--chunksize', type=int, default=10000)
parser.add_argument('--drop', action='store_true', help='Drop target table before import')
args = parser.parse_args()

# Connect to sqlite
sconn = sqlite3.connect(args.sqlite)
sconn.row_factory = None
scur = sconn.cursor()

# Connect to Postgres
pconn = psycopg2.connect(args.pg)
pcur = pconn.cursor()

if args.drop:
    pcur.execute('DROP TABLE IF EXISTS stock_data')
    pconn.commit()

pcur.execute(CREATE_TABLE_SQL)
pconn.commit()

# Count rows
scur.execute('SELECT COUNT(*) FROM stock_data')
total = scur.fetchone()[0]
print(f'Total rows in sqlite: {total}')

offset = 0
batch = args.chunksize
while True:
    scur.execute('SELECT code,date,open,high,low,close,volume,amount FROM stock_data ORDER BY rowid LIMIT ? OFFSET ?', (batch, offset))
    rows = scur.fetchall()
    if not rows:
        break
    # Use psycopg2 execute_values for fast bulk insert
    execute_values(pcur, INSERT_SQL, rows, page_size=1000)
    pconn.commit()
    offset += len(rows)
    print(f'Imported {offset}/{total}')

scur.close()
sconn.close()
pcur.close()
pconn.close()
print('Migration complete.')
