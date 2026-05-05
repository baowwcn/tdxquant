"""
Query stock data from SQLite database to CSV file.

Usage:
    python query_stock_to_csv.py --code 688693.SH --start 2025-06-01 --end 2026-03-09 --output C:/stock

Parameters:
    --code    : Stock code (e.g., 688693.SH, 000001.SZ)
    --start   : Start date (YYYY-MM-DD)
    --end     : End date (YYYY-MM-DD)
    --db      : Database path (default: a_share_full.db)
    --output  : Output directory (default: current directory)
"""

import sqlite3
import pandas as pd
import argparse


def query_stock_to_csv(
    code, start_date, end_date, db_path="a_share_full.db", output_dir="."
):
    conn = sqlite3.connect(db_path)
    query = f"""
    SELECT code, date, open, high, low, close, volume, amount 
    FROM stock_data 
    WHERE code = '{code}' AND date BETWEEN '{start_date}' AND '{end_date}' 
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))

    output_file = f"{output_dir}/{code}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nTotal records: {len(df)}")
    print(f"Saved to: {output_file}")
    conn.close()
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query stock data to CSV")
    parser.add_argument("--code", required=True, help="Stock code (e.g., 688693.SH)")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--db", default="a_share_full.db", help="Database path")
    parser.add_argument("--output", default=".", help="Output directory")

    args = parser.parse_args()
    query_stock_to_csv(args.code, args.start, args.end, args.db, args.output)
