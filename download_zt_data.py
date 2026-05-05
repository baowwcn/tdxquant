import sys, os
import winreg
import time

key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq
import pandas as pd

tq.initialize(__file__)

stocks = tq.get_stock_list_in_sector("ZT", block_type=1)
if not stocks:
    with open("zt_stocks_2026-04-14.txt", "r", encoding="utf-8") as f:
        stocks = []
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2 and (
                parts[1].endswith(".SZ") or parts[1].endswith(".SH")
            ):
                stocks.append(parts[1])

print(f"共 {len(stocks)} 只股票")

output_dir = "cvs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

start_date = "20251015"
end_date = "20260420"

print(f"\n下载: {start_date} ~ {end_date}")

success = 0
for i, code in enumerate(stocks, 1):
    try:
        result = tq.get_market_data(
            stock_list=[code], period="1d", start_time=start_date, end_time=end_date
        )

        if not result or "Close" not in result:
            print(f"{i}. {code}: 无数据")
            continue

        close_df = result["Close"]
        if close_df.empty:
            print(f"{i}. {code}: 空数据")
            continue

        # 转换格式: 每列是一个股票，合并所有列
        df = pd.DataFrame()
        for col in result.keys():
            field_df = result[col]
            if not field_df.empty:
                df[col] = field_df[col]

        if not df.empty and len(df) > 0:
            df.index = close_df.index
            filename = os.path.join(output_dir, f"{code}.csv")
            df.to_csv(filename, encoding="utf-8")
            print(f"{i}. {code}: {len(df)} 条")
            success += 1
        else:
            print(f"{i}. {code}: 无有效数据")

        time.sleep(0.1)

    except Exception as e:
        print(f"{i}. {code}: 错误 - {e}")

tq.close()

print(f"\n完成! 成功 {success}/{len(stocks)}")
print(f"保存在: {output_dir}/")
