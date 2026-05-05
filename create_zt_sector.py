import sys, os
import winreg
import time

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq

tq.initialize(__file__)

# 读取涨停股票列表
zt_codes = []
try:
    with open("zt_stocks_2026-04-14.txt", "r", encoding="utf-8") as f:
        for line in f:
            if ".SZ" in line or ".SH" in line:
                code = line.split()[1]
                zt_codes.append(code)
except:
    pass

if not zt_codes:
    stock_list = tq.get_stock_list(market="5", list_type=0)
    for i in range(0, len(stock_list), 50):
        for code in stock_list[i : i + 50]:
            info = tq.get_more_info(code, ["FCAmo"])
            try:
                if float(info.get("FCAmo", "0")) > 0:
                    zt_codes.append(code)
            except:
                pass
        time.sleep(0.03)

# 使用 create_sector 创建板块
block_name = "今日涨停"
result = tq.create_sector(block_name)
print(f"create_sector: {result}")

# 需要在客户端确认后，发送股票到板块
if zt_codes:
    result2 = tq.send_user_block(block_name, zt_codes, show=False)
    print(f"send_user_block: {result2}")

# 等待一下然后查询
time.sleep(1)

# 查询是否创建成功
sectors = tq.get_user_sector()
for s in sectors:
    print(s)

tq.close()
print(f"\n完成！已发送 {len(zt_codes)} 只股票到 '{block_name}' 板块")
print("请在通达信客户端确认板块创建操作")
