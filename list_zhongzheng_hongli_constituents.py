import sys, io

sys.path.insert(0, "C:/new_tdx64/PYPlugins/user")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from tqcenter import tq
import json, datetime

tq.initialize("dummy.py")

INDEX_CODE = "000922.SH"

# ── Part 1: Get index constituents ──
print(f"中证红利指数 (000922) 成分股\n{'=' * 50}")

stocks = tq.get_stock_list_in_sector(INDEX_CODE, block_type=0, list_type=1)
print(f"共 {len(stocks)} 只成分股\n")

# Sort by market cap (Zsz) descending and show top 30
all_data = []
n = len(stocks)
for i, s in enumerate(stocks):
    code = s["Code"]
    name = s["Name"]
    more = tq.get_more_info(code, ["Zsz", "Ltsz", "ZAF", "DynaPE", "fHSL"])
    zsz = more.get("Zsz", 0)
    ltsz = more.get("Ltsz", 0)
    zaf = more.get("ZAF", 0)
    pe = more.get("DynaPE", 0)
    hsl = more.get("fHSL", 0)
    all_data.append(
        {
            "code": code,
            "name": name,
            "zsz": zsz,
            "ltsz": ltsz,
            "zaf": zaf,
            "pe": pe,
            "hsl": hsl,
        }
    )
    if (i + 1) % 30 == 0:
        print(f"  已处理 {i + 1}/{n}...")

# Sort by market cap descending
all_data.sort(
    key=lambda x: float(x["zsz"]) if x["zsz"] and x["zsz"] != "--" else 0, reverse=True
)

print(f"\n前30大重仓股（按总市值排序，作为ETF配置比例参考）")
print(
    f"{'代码':<12} {'名称':<10} {'总市值(亿)':<12} {'流通市值(亿)':<14} {'涨幅%':<8} {'市盈率':<8} {'换手%':<8}"
)
print("-" * 72)
for d in all_data[:30]:
    zsz = f"{float(d['zsz']):.1f}" if d["zsz"] and d["zsz"] != "--" else "--"
    ltsz = f"{float(d['ltsz']):.1f}" if d["ltsz"] and d["ltsz"] != "--" else "--"
    zaf = f"{float(d['zaf']):.2f}" if d["zaf"] and d["zaf"] != "--" else "--"
    pe = f"{float(d['pe']):.1f}" if d["pe"] and d["pe"] != "--" else "--"
    hsl = f"{float(d['hsl']):.2f}" if d["hsl"] and d["hsl"] != "--" else "--"
    print(
        f"{d['code']:<12} {d['name']:<8} {zsz:<12} {ltsz:<14} {zaf:<8} {pe:<8} {hsl:<8}"
    )

# ── Part 2: Try fund-specific fields ──
print(f"\n\nETF基金特定字段查询\n{'=' * 50}")

# Try GP fields related to fund holdings
fund_fields = ["GP01", "GP02", "GP03", "GP04", "GP05"]
print("\n尝试GP字段 for 515180.SH:")
try:
    gp_data = tq.get_gpjy_value(
        ["515180.SH"], fund_fields, start_time="20260101", end_time="20260527"
    )
    if gp_data:
        print(json.dumps(gp_data, ensure_ascii=False)[:200])
except Exception as e:
    print(f"  GP fields error: {e}")

# Try GO fields
go_fields = ["GO01", "GO02", "GO03"]
print("\n尝试GO字段 for 515180.SH:")
try:
    go_data = tq.get_gp_one_data(["515180.SH"], go_fields)
    if go_data:
        print(json.dumps(go_data, ensure_ascii=False)[:200])
    else:
        print("  empty")
except Exception as e:
    print(f"  GO fields error: {e}")

# Try more_info with many fields
info_fields = [
    "F001",
    "F002",
    "F003",
    "F004",
    "F005",
    "F006",
    "F007",
    "F008",
    "F009",
    "F010",
    "F011",
    "F012",
    "F013",
    "F014",
    "F015",
    "F016",
    "F017",
    "F018",
    "F019",
    "F020",
    "F021",
    "F022",
    "F023",
    "F024",
    "F025",
    "F026",
    "F027",
    "F028",
    "F029",
    "F030",
    "F100",
    "F101",
    "F102",
    "F103",
    "F104",
    "F105",
    "F106",
    "F107",
    "F108",
    "F109",
    "F110",
    "F111",
    "F112",
]
print(f"\n尝试更多 get_more_info 字段:")
more = tq.get_more_info("515180.SH", info_fields)
if more:
    for k, v in more.items():
        print(f"  {k}: {v}")

# Try stock info fields
print(f"\n尝试 get_stock_info:")
info = tq.get_stock_info("515180.SH", ["name", "code", "market", "type"])
if info:
    print(json.dumps(info, ensure_ascii=False)[:200])

# Try gb_info
try:
    gb = tq.get_gb_info("515180.SH", ["20260527"], 1)
    print(f"\nget_gb_info: {json.dumps(gb, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"\nget_gb_info error: {e}")

# Save full list to CSV
import csv

today = datetime.date.today().strftime("%Y%m%d")
csv_file = f"中证红利成分股_{today}.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(
        ["代码", "名称", "总市值(亿)", "流通市值(亿)", "涨幅%", "市盈率", "换手率%"]
    )
    for d in all_data:
        w.writerow(
            [d["code"], d["name"], d["zsz"], d["ltsz"], d["zaf"], d["pe"], d["hsl"]]
        )
print(f"\n已保存完整数据到: {csv_file}")

tq.close()
