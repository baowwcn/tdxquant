# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese A-share (A股) stock market data analysis project using the Tdx (通达信) terminal. It imports, stores, and analyzes stock market data.

## Key Technologies

- **TdxQuant DLL** (`TPythClient.dll`) - Connects to local Tdx terminal via ctypes
- **tqcenter.py** - Python wrapper around the DLL, provides `tq` object with methods like `tq.get_market_data()`, `tq.get_stock_list()`, `tq.initialize()`
- **SQLite** - Stores historical stock data in `a_share_full.db` and `a_share_monthly.db`
- **pandas/numpy** - Data processing

## Database Schema

Both `stock_data` tables use the same schema:
- `code` TEXT - Stock code (e.g., `000001.SZ`, `600000.SH`)
- `date` TEXT - Trade date (YYYY-MM-DD)
- `open`, `high`, `low`, `close` REAL - Prices in yuan
- `volume` REAL - Volume in lots (100 shares)
- `amount` REAL - Turnover in yuan

## Common Commands

```bash
# Import from local Tdx vipdoc files (binary .day files)
python import_tdx_vipdoc_to_sqlite.py
python import_tdx_vipdoc_to_sqlite.py --last-month    # recent data only
python import_tdx_vipdoc_to_sqlite.py --last-year
python import_tdx_vipdoc_to_sqlite.py --start-date 2020-01-01 --end-date 2024-12-31
python import_tdx_vipdoc_to_sqlite.py --vipdoc-root "D:\tdx" --db "\\server\path\a_share_full.db"

# Build full history database via TdxQuant API (requires Tdx terminal running)
python build_ashare_history_db.py

# Update monthly database via API
python store_a_share_data.py

# Query database directly
python query_a_share_db.py --db a_share_full.db

# Query via inline Python
python -c "import sqlite3, pandas as pd; conn = sqlite3.connect('a_share_full.db'); df = pd.read_sql_query(\"SELECT * FROM stock_data WHERE code='000002.SZ' AND date LIKE '2024%'\", conn); print(df)"
```

## Architecture

```
TPythClient.dll          <- Binary DLL (Windows only, in parent dir)
    ↓ ctypes
tqcenter.py              <- Main API wrapper (tq object)
    ├── get_stock_list()     - Get all stocks
    ├── get_market_data()    - K-line/OHLCV data
    ├── refresh_cache()      - Refresh terminal cache
    └── initialize()        - Connect to terminal

import_tdx_vipdoc_to_sqlite.py  <- Reads .day files from C:\new_tdx64\vipdoc\
build_ashare_history_db.py     <- Uses tqcenter API
store_a_share_data.py           <- Uses tqcenter API (monthly data)

SQLite: a_share_full.db (1990-present, 2300万+ records)
        a_share_monthly.db (recent month)
```

## Stock Code Conventions

- Shanghai: `.SH` suffix (e.g., `600000.SH`)
- Shenzhen: `.SZ` suffix (e.g., `000001.SZ`)
- Beijing: `.BJ` suffix
- TdxQuant internal format: `market_code#stock_code` (e.g., `0#600000` for SZ, `1#600000` for SH)

## Data Sources

1. **Local vipdoc files** (`C:\new_tdx64\vipdoc\sh\lday\`, `vipdoc\sz\lday\`) - Binary `.day` files, 32 bytes/record
2. **TdxQuant API** - Requires Tdx terminal to be running and logged in

## File Locations

- `TdxQuant/*.md` - Chinese documentation (version history, API reference, FAQs)
- `ztb/` - 涨停板 (limit-up stock) analysis output files
- `data/ashare_daily/` - Individual stock CSV files
- `tdx_quant_md/`, `tdx_quant_site/` - Documentation site files
