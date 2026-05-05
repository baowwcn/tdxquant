import sys, os
import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 直接使用 send_user_block 发送到新板块 (block_code为空表示新建)
block_code = ""
zt_codes = [
    "000056.SZ",
    "000539.SZ",
    "000690.SZ",
    "000802.SZ",
    "001268.SZ",
    "002081.SZ",
]

result = tq.send_user_block(block_code, zt_codes, show=True)
print(f"发送结果: {result}")

tq.close()
