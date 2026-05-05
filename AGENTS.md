# AGENTS.md - TdxQuant 通达信量化平台

## Overview
Python quantitative trading framework connecting to TongDaXin terminal via `TPythClient.dll`. No formal package manager - dependencies are ad-hoc.

## Prerequisites
- **TongDaXin terminal must be running** with TQ strategy functionality enabled (金融终端/量化模拟版/专业研究版)
- Required DLL: `TPythClient.dll` at `D:\new_tdx_mock\TPythClient.dll`
- Python 3.7-3.14 (recommend 3.13)
- Required packages: `numpy`, `pandas` (install via pip/conda as needed)

## Running Scripts
```python
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq

tq.initialize(__file__)  # Initialize connection
# ... your code ...
tq.close()  # Always close connection
```

## Key Entry Points
- `tqcenter.py`: Core API (`tq` class, `tqconst` constants)
- `tqtrade.py`: Trading wrapper with order/position functions
- `test.py`: Example strategy using stock screening

## Supported Data Types
- A股 (SZ/SH), 港股 (HK), 美股 (US), 期货 (SHF/DCE/CZC/CFF), 期权, 指数 (CSI/CNI)
- Format: `600000.SH`, `000001.SZ`, `00700.HK`, `AAPL.US`, `CU2409.SHF`

## Code Validation
Use `tq.check_stock_code_format(code)` to validate symbol format.

## Debug Notes
- Stock code validation: `_is_valid_symbol_code()` rejects invalid formats early
- DLL path auto-resolved from `global_dll_path` in tqcenter.py
- Use `tq.initialize(__file__)` or explicit path - must point to a file, not just directory