import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "C:/new_tdx64/PYPlugins/user")
from tqcenter import tq

CODE = sys.argv[1] if len(sys.argv) > 1 else "000001.SZ"
tq.initialize(__file__)

periods = [
    (2025, 630, "2025H1"),
    (2025, 930, "2025Q3"),
    (2025, 1231, "2025A"),
    (2026, 331, "2026Q1"),
]

# 股东相关字段
fields = ["FN238", "FN239", "FN242", "FN243", "FN244", "FN245", "FN264", "FN265"]
labels = [
    "总股本",
    "流通A股",
    "股东人数",
    "第一大股东持股",
    "十大流通股东合计",
    "十大股东合计",
    "十大流通股东A股合计",
    "第一大流通股东持股",
]

print("报告期\t" + "\t".join(labels))
for y, md, period in periods:
    fd = tq.get_financial_data_by_date([CODE], fields, year=y, mmdd=md)
    d = fd.get(CODE, {})
    vals = []
    for f in fields:
        v = d.get(f, "--")
        if v != "--":
            v = f"{float(v):,.0f}"
        vals.append(v)
    print(f"{period}\t" + "\t".join(vals))

tq.close()
