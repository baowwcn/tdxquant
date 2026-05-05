import sys, os
import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 不指定field_list
stock_code = "000001.SZ"
result = tq.get_market_data(
    stock_list=[stock_code], period="1d", start_time="20251015", end_time="20260420"
)
print(f"结果: {type(result)}")
if result:
    for k, v in result.items():
        print(f"Key: {k}")
        if isinstance(v, dict):
            print(f"  内容: {v}")
        elif hasattr(v, "head"):
            print(f"  数据: {v.shape}")
            print(v.head())

tq.close()
