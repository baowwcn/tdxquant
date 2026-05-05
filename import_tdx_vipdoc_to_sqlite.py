import os
import sqlite3
import struct
import sys
from pathlib import Path
from datetime import datetime, timedelta

TDX_ROOT = Path(r'C:\new_tdx64')
DB_PATH = Path(__file__).resolve().parent / 'a_share_full.db'

RECORD_SIZE = 32
RECORD_FORMAT = '<iiiii f ii'  # date, open, high, low, close, amount(float), volume, unused


def parse_day_file(file_path: Path, start_date=None, end_date=None):
    with file_path.open('rb') as f:
        data = f.read()

    records = []
    total = len(data) // RECORD_SIZE
    exchange = file_path.parent.parent.name.upper()
    suffix = '.SZ' if exchange == 'SZ' else '.SH'
    for i in range(total):
        start = i * RECORD_SIZE
        rec = data[start:start + RECORD_SIZE]
        if len(rec) != RECORD_SIZE:
            continue
        date_int, open_raw, high_raw, low_raw, close_raw, amount, volume, _unused = struct.unpack(RECORD_FORMAT, rec)
        date_str = f'{date_int:08d}'
        date_formatted = date_str[:4] + '-' + date_str[4:6] + '-' + date_str[6:]

        # 过滤日期范围
        if start_date and date_formatted < start_date:
            continue
        if end_date and date_formatted > end_date:
            continue

        records.append((
            file_path.stem[2:] + suffix,
            date_formatted,
            open_raw / 100.0,
            high_raw / 100.0,
            low_raw / 100.0,
            close_raw / 100.0,
            float(volume),
            float(amount),
        ))
    return records


def clean_old_data(conn, start_date, end_date):
    """清理超出时间范围的数据"""
    if start_date:
        conn.execute('DELETE FROM stock_data WHERE date < ?', (start_date,))
        deleted = conn.execute('SELECT changes()').fetchone()[0]
        print(f'Cleaned {deleted} records before {start_date}')

    if end_date:
        conn.execute('DELETE FROM stock_data WHERE date > ?', (end_date,))
        deleted = conn.execute('SELECT changes()').fetchone()[0]
        print(f'Cleaned {deleted} records after {end_date}')

    conn.commit()


def build_database(start_date=None, end_date=None, keep_only_range=False, db_path=None, vipdoc_root=None):
    tdx_root = Path(vipdoc_root) if vipdoc_root else TDX_ROOT
    vipdoc_dir = tdx_root / 'vipdoc'
    if not vipdoc_dir.exists():
        raise FileNotFoundError(f'vipdoc directory not found at {vipdoc_dir}')

    sh_dir = vipdoc_dir / 'sh' / 'lday'
    sz_dir = vipdoc_dir / 'sz' / 'lday'
    if not sh_dir.exists() or not sz_dir.exists():
        raise FileNotFoundError('Could not find sh/lday or sz/lday directories under vipdoc')

    day_files = sorted(sh_dir.glob('sh*.day')) + sorted(sz_dir.glob('sz*.day'))
    if not day_files:
        raise FileNotFoundError('No .day files found in vipdoc/sh/lday or vipdoc/sz/lday')

    print(f'Found {len(day_files)} .day files to import')
    if start_date:
        print(f'Filtering data from {start_date}')
    if end_date:
        print(f'Filtering data to {end_date}')
    if keep_only_range:
        print('Will keep only data within the specified range')

    db_path = Path(db_path) if db_path else DB_PATH
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute('PRAGMA journal_mode=WAL')
    except sqlite3.OperationalError:
        print('Warning: WAL mode not supported on this database path, using default journal mode.')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=100000')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS stock_data (
        code TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        amount REAL,
        PRIMARY KEY (code, date)
    )
    ''')
    conn.commit()

    # 如果需要只保留范围内的数据，先清理旧数据
    if keep_only_range:
        clean_old_data(conn, start_date, end_date)

    insert_sql = '''
    INSERT OR REPLACE INTO stock_data
    (code, date, open, high, low, close, volume, amount)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''

    total_rows = 0
    for idx, file_path in enumerate(day_files, start=1):
        print(f'[{idx}/{len(day_files)}] Importing {file_path.name}...')
        records = parse_day_file(file_path, start_date, end_date)
        if records:
            conn.executemany(insert_sql, records)
            conn.commit()
            total_rows += len(records)
            print(f'  imported {len(records)} rows')
        else:
            print('  no records found or file empty')

    conn.close()
    print(f'Import complete. Total rows imported: {total_rows}')
    print(f'Database file: {db_path}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Import TDX vipdoc data to SQLite database')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)', default=None)
    parser.add_argument('--db', help='SQLite database path to use. Default: a_share_full.db in the current folder')
    parser.add_argument('--vipdoc-root', help=r'通达信安装目录根路径，默认 C:\new_tdx64')
    parser.add_argument('--keep-only-range', action='store_true',
                       help='Keep only data within the specified date range (delete others)')

    # 预设选项
    parser.add_argument('--last-month', action='store_true', help='Import last month data')
    parser.add_argument('--last-year', action='store_true', help='Import last year data')
    parser.add_argument('--last-3years', action='store_true', help='Import last 3 years data')

    args = parser.parse_args()

    # 处理预设选项
    today = datetime.now()
    if args.last_month:
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        keep_only_range = False
    elif args.last_year:
        start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        keep_only_range = False
    elif args.last_3years:
        start_date = (today - timedelta(days=365*3)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        keep_only_range = False
    else:
        start_date = args.start_date
        end_date = args.end_date
        keep_only_range = args.keep_only_range

    build_database(
        start_date=start_date,
        end_date=end_date,
        keep_only_range=keep_only_range,
        db_path=args.db,
        vipdoc_root=args.vipdoc_root,
    )
