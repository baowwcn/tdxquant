# AGENTS.md

## Prerequisite

**TdxW.exe must be running and logged in** — all API calls via `tqcenter.py` require an active terminal session.

## Python Environment

- Python 3.14 (uv-managed venv): `.venv\Scripts\python.exe`
- No `pyproject.toml`, no test framework, no linter/formatter config — vanilla scripts only

## TdxQuant Setup (Mandatory)

Two path-import patterns are used in this repo:

**Pattern A — Hardcoded path (most scripts):**
```python
import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')     # MUST be insert(0), not append
from tqcenter import tq
tq.initialize('dummy.py')                                # Use 'dummy.py', not __file__
```

**Pattern B — Registry auto-detect (scripts that manipulate TDX sectors):**
```python
import sys, os, winreg
key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))
from tqcenter import tq
tq.initialize(__file__)                                  # Uses __file__ here
```

The DLL itself loads from `C:/new_tdx64/TPythClient.dll` (hardcoded in `tqcenter.py:26`).

## API Return Format

`get_market_data()` → `dict[FieldName → DataFrame]`:
- Keys: `'Close'`, `'Open'`, `'High'`, `'Low'`, `'Volume'`, `'Amount'`
- Values: DataFrames with **stock codes as columns**, dates as index
- Access: `result['Close']['002758.SZ']` for a single stock series

## Quick Reference

| Task | Code |
|------|------|
| Historical K-line | `tq.get_market_data(['Close'], ['002758.SZ'], '1d', count=5)` |
| Real-time snapshot | `tq.get_market_snapshot('002758.SZ')` — Amount in 万元 |
| Limit-up check | `tq.get_more_info('002758.SZ', ['FCAmo'])` — `FCAmo > 0` = 涨停 |
| All A-share stocks | `tq.get_stock_list(market='5')` |
| User sector stocks | `tq.get_stock_list_in_sector(code, block_type=1)` |
| Create sector | `tq.create_sector(name)` then `tq.send_user_block(name, codes, show=False)` |

## Stock Codes

- `600000.SH` (Shanghai), `000001.SZ` (Shenzhen), `.BJ` (Beijing)
- TdxQuant internal: `market_code#stock_code` (e.g. `0#600000`, `1#600000`)

## Key Scripts

| Script | Purpose |
|--------|---------|
| `import_tdx_vipdoc_to_sqlite.py` | Import from binary `.day` files at `C:\new_tdx64\vipdoc\` → `a_share_full.db` |
| `build_ashare_history_db.py` | Download full history via API → `data/ashare_daily/*.csv` |
| `store_a_share_data.py` | Download recent month via API → `a_share_monthly.db` |
| `query_a_share_db.py` | CLI query tool for any DB |
| `list_zt_stocks.py` | List stocks in "ZTB" (涨停板) sector |
| `realtime_alert_vol_open5.py` | Real-time volume alert (needs DingTalk token) |
| `dingtalk_send.py` | Hardcoded webhook token — **do not commit to public repos** |
| `ma_parallel_bt.py` | MA slope parallel backtest |
| `ztb_analysis.py` | Limit-up feature analysis from `ztb/*.csv` |
| `tqcenter.py` | Core TdxQuant wrapper (3233 lines, v1.0.4) |
| `个股机构持股情况.py` | Institutional holdings query |
| `前十大股东情况.py` | Top-10 shareholder aggregate data |
| `query_etf_515180_holdings.py` | 515180.SH 红利ETF持仓 + `--holder` 持有人结构 |
| `query_etf_512170_holdings.py` | 512170.SH 医疗ETF持仓 + `--holder` 持有人结构 |
| `query_etf_515220_holdings.py` | 515220.SH 煤炭ETF持仓 + `--holder` 持有人结构 |
| `query_etf_holdings.py` | 通用ETF查询脚本: `python query_etf_holdings.py <CODE> [--holder]` |
| `.opencode/skills/inst-holder/` | Skill: inst-holder (load via `skill` tool) |

## Database Schema

```sql
-- Used by: a_share_full.db, a_share_monthly.db
CREATE TABLE stock_data (
    code TEXT, date TEXT, open REAL, high REAL, low REAL,
    close REAL, volume REAL, amount REAL,
    PRIMARY KEY (code, date)
);
```

- `a_share_full.db`: ~1990-present, 2300万+ records (gitignored)
- `a_share_monthly.db`: Recent month only (gitignored)
- Volume in **lots** (100 shares), not shares

## Known Constraints

1. **Windows-only** — Uses `TPythClient.dll` via ctypes
2. **Login required** — Terminal must be logged in, not just running
3. **Amount unit** — `get_market_snapshot` returns 万元 (×10000 for yuan)
4. **Date format** — `count=N` for recent N bars; `"YYYYMMDD"` (no dashes) for specific dates
5. **DingTalk token** — Hardcoded in `dingtalk_send.py:5`; replace if rotated
6. **No linter/tests/build** — Scripts are standalone; no CI/CD
7. **`get_stock_list_in_sector` with index codes (000xxx/399xxx) is broken** — all return the same 198 stocks regardless of input
8. **`get_trackzs_etf_info` works** — e.g. `000300.SH` returns 30 ETFs tracking 沪深300; `000922.SH` returns none (中证红利 not in system)
9. **No ETF portfolio/constituent API in TdxQuant** — use EastMoney API for holdings data
10. **ETF holder structure** — `python query_etf_515180_holdings.py --holder` fetches from EastMoney `type=cyrjg` (no TdxW login required)
