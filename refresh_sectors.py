import sys, os
import winreg
import time

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 刷新缓存
tq.refresh_cache(market="AG", force=True)
time.sleep(2)

# 重新获取板块列表
sectors = tq.get_user_sector()
print("用户自定义板块列表:")
for s in sectors:
    print(f"  {s['Code']} - {s['Name']}")

# 检查"今日涨停"板块
for s in sectors:
    if "涨停" in s.get("Name", ""):
        print(f"\n找到板块: {s}")

tq.close()
