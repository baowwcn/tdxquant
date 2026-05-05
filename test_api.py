import sys, os
import winreg
import time

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 测试获取数据格式
stock_code = "000001.SZ"
result = tq.get_market_data(
    stock_list=[stock_code],
    period="1d",
    start_time="20251015",
    end_time="20260420",
    count=10,
)
print(f"返回类型: {type(result)}")
if result and stock_code in result:
    df = result[stock_code]
    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(df.head())

tq.close()
