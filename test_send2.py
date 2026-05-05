import sys, os
import winreg
import time

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 先清理已有板块中的股票
block_name = "JRZT"  # 简写

# 尝试发送股票到板块
file_path = "zt_stocks_2026-04-14.txt"
zt_codes = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.split()
        if len(parts) >= 2:
            code = parts[1]
            if code.endswith(".SZ") or code.endswith(".SH"):
                zt_codes.append(code)

print(f"读取到 {len(zt_codes)} 只涨停股票")

# 发送股票 - 使用 send_to_tdx 功能更直接
# 直接发送到客户端显示的板块编辑器
for code in zt_codes[:10]:
    result = tq.send_user_block("", [code], show=True)
    print(f"发送 {code}: {result}")
    time.sleep(0.1)

tq.close()
print("\n完成！")
