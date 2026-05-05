# AGENTS.md

## Quick Start

**Requires Tdx terminal running** - All API calls via `tqcenter.py` need `TdxW.exe` process active and logged in.

```bash
# Use virtual environment
.venv\Scripts\python.exe your_script.py
# Or via poetry
poetry run python your_script.py
```

## TdxQuant API Setup (CRITICAL)

```python
import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')  # MUST use insert(0), not append
from tqcenter import tq
tq.initialize('dummy.py')  # Use dummy.py, not __file__
```

## API Return Format

`get_market_data()` returns `dict[FieldName -> DataFrame]`:
- Keys: 'Close', 'Open', 'High', 'Low', 'Volume', 'Amount'
- Values: DataFrame with **stock codes as columns**, dates as index
- Access: `result['Close']['002758.SZ']` to get single stock data

## Key Patterns

| Task | Code |
|------|------|
| Historical K-line | `tq.get_market_data(['Close'], ['002758.SZ'], '1d', count=5)` |
| Real-time snapshot | `tq.get_market_snapshot('002758.SZ')` |
| Limit-up check | `tq.get_more_info('002758.SZ', ['FCAmo'])` — FCAmo > 0 = 涨停 |
| User-defined sector | `tq.get_stock_list_in_sector(code, block_type=1)` — **block_type=1 required** |

## Known Constraints

1. **Windows-only** - Uses `TPythClient.dll` via ctypes
2. **TdxQuant requires login** - Terminal must be logged in, not just running
3. **Stock codes** - Use `.SH`/`.SZ` suffix (e.g., `600000.SH`, `000001.SZ`)
4. **Amount unit** - `get_market_snapshot` returns 万元, multiply by 10000 for yuan
5. **Date format** - Use `count=N` for recent N bars; use "YYYYMMDD" (no dashes) for specific dates

## Skills

Use `skill` tool to load:
- `tdx-tq` - Full TdxQuant API documentation
- `tdx-quote` - Query stock quote data (K-line, snapshot, real-time)
- `zt-feature` - Analyze limit-up stock patterns (MA, volume)
- `test` - Test skill

## Reference

- `.opencode/skills/` - All OpenCode skills
- `CLAUDE.md` - Detailed project context