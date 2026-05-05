import sys, os
import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

stocks = tq.get_stock_list_in_sector("ZTB", block_type=1)
print(f"涨停板块(ZTB)共 {len(stocks)} 只股票:\n")

for i, code in enumerate(stocks, 1):
    info = tq.get_stock_info(code, ["Name"])
    name = info.get("Name", "N/A") if info else "N/A"
    print(f"{i}. {code} {name}")

tq.close()
