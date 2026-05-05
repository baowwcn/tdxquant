import sys, os

import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 尝试不同block_type
for bt in [0, 1]:
    print(f"=== block_type={bt} ===")
    stocks = tq.get_stock_list_in_sector("ZTB", block_type=bt)
    print(f"数量: {len(stocks)}")
    if stocks:
        print(stocks[:10])
    print()

tq.close()
