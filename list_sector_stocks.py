import sys, os

import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 尝试不同板块
for sector in ["ZTB", "QS", "BUY", "ZZT"]:
    print(f"\n=== {sector} 板块 ===")
    result = tq.get_stock_list_in_sector(sector, block_type=0)
    if result:
        print(result[:5] if len(result) > 5 else result)
    else:
        # 尝试 block_type=1
        result = tq.get_stock_list_in_sector(sector, block_type=1)
        print(result[:5] if len(result) > 5 else result)

tq.close()
