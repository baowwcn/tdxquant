import sys, os

# 方式一：自动从注册表读取（推荐）
import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 获取用户自选股板块列表
result = tq.get_user_sector()
print("用户自定义板块列表:")
print(result)

tq.close()
