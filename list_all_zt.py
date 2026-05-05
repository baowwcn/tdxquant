import sys, os
import winreg

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq
import time

tq.initialize(__file__)

stock_list = tq.get_stock_list(market="5", list_type=0)
print(f"共 {len(stock_list)} 只股票")

print("\n检测涨停股票...")
zt_stocks = []
batch_size = 50

for i in range(0, len(stock_list), batch_size):
    batch = stock_list[i : i + batch_size]
    for code in batch:
        info = tq.get_more_info(code, ["FCAmo", "Name", "Now", "ZTPrice"])
        fcamo = info.get("FCAmo", "0")
        try:
            fcamo_val = float(fcamo) if fcamo else 0
        except:
            fcamo_val = 0
        if fcamo_val > 0:
            name = info.get("Name", "")
            if not name:
                info2 = tq.get_stock_info(code, ["Name"])
                name = info2.get("Name", "") if info2 else ""
            now = info.get("Now", "0")
            if not now or now == "0":
                snap = tq.get_market_snapshot(code)
                now = snap.get("Now", "") if snap else ""
            ztPrice = info.get("ZTPrice", "")
            zt_stocks.append(
                {
                    "code": code,
                    "name": name,
                    "price": now,
                    "ztPrice": ztPrice,
                }
            )

    if (i + batch_size) % 500 == 0:
        print(f"已处理 {min(i + batch_size, len(stock_list))}/{len(stock_list)} 只...")
    time.sleep(0.05)

tq.close()

output_file = "zt_stocks_2026-04-14.txt"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"2026-04-14 今日涨停板共 {len(zt_stocks)} 只\n")
    f.write("=" * 50 + "\n\n")
    for i, stock in enumerate(zt_stocks, 1):
        f.write(
            f"{i}. {stock['code']} {stock['name']} 现价:{stock['price']} 涨停价:{stock['ztPrice']}\n"
        )

print(f"\n已保存到 {output_file}")
print(f"涨停板共 {len(zt_stocks)} 只")
