import sys, os
import winreg
import time

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 读取涨停股票
file_path = "zt_stocks_2026-04-14.txt"
zt_codes = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 2 and (parts[1].endswith(".SZ") or parts[1].endswith(".SH")):
            zt_codes.append(parts[1])

print(f"读取 {len(zt_codes)} 只涨停股票")

# 发送到现有的 ZT 板块
result = tq.send_user_block("ZT", zt_codes, show=True)
print(f"发送到ZT板块: {result}")

# 获取结果
time.sleep(1)
stocks = tq.get_stock_list_in_sector("ZT", block_type=1)
print(f"\nZT板块现有 {len(stocks)} 只股票")

tq.close()
print(f"\n完成！已更新ZT(涨停)板块，共 {len(zt_codes)} 只涨停股票")
