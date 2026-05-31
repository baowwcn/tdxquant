import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "C:/new_tdx64/PYPlugins/user")
from tqcenter import tq

CODE = sys.argv[1] if len(sys.argv) > 1 else "002758.SZ"
tq.initialize(__file__)

periods = [
    (2023, 1231, "2023A"),
    (2024, 331, "2024Q1"),
    (2024, 630, "2024H1"),
    (2024, 930, "2024Q3"),
    (2024, 1231, "2024A"),
    (2025, 331, "2025Q1"),
    (2025, 630, "2025H1"),
    (2025, 930, "2025Q3"),
    (2025, 1231, "2025A"),
    (2026, 331, "2026Q1"),
]

fields = [
    "FN246",
    "FN247",
    "FN248",
    "FN249",
    "FN254",
    "FN255",
    "FN256",
    "FN257",
    "FN258",
    "FN259",
]
labels = [
    "机构总数",
    "机构持股(股)",
    "QFII家数",
    "QFII持股(股)",
    "基金家数",
    "基金持股(股)",
    "社保家数",
    "社保持股(股)",
    "私募家数",
    "私募持股(股)",
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
