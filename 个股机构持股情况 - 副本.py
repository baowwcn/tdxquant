import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, "C:/new_tdx64/PYPlugins/user")
from tqcenter import tq

# ── 配置 ──────────────────────────────────
CODE = "300373.SZ"
# ─────────────────────────────────────────

tq.initialize(__file__)

periods = [
    (2025, 630, "2025H1"),
    (2025, 930, "2025Q3"),
    (2025, 1231, "2025A"),
    (2026, 331, "2026Q1"),
]

fields = [
    ("FN246", "机构总数(家)"),
    ("FN247", "机构持股(股)"),
    ("FN254", "基金家数"),
    ("FN255", "基金持股(股)"),
    ("FN256", "社保家数"),
    ("FN257", "社保持股(股)"),
    ("FN258", "私募家数"),
    ("FN259", "私募持股(股)"),
    ("FN250", "券商家数"),
    ("FN251", "券商持股(股)"),
    ("FN252", "保险家数"),
    ("FN253", "保险持股(股)"),
]

field_names = [f[0] for f in fields]

print("报告期\t机构总数\t机构持股(股)\t基金家数\t基金持股(股)\t社保\t私募")
for y, md, period in periods:
    fd = tq.get_financial_data_by_date([CODE], field_names, year=y, mmdd=md)
    d = fd.get(CODE, {})
    fn246 = f"{float(d.get('FN246', 0)):.0f}"
    fn247 = f"{float(d.get('FN247', 0)):,.0f}"
    fn254 = f"{float(d.get('FN254', 0)):.0f}"
    fn255 = f"{float(d.get('FN255', 0)):,.0f}"
    shebao = f"{float(d.get('FN257', 0)):,.0f}"
    simu = f"{float(d.get('FN259', 0)):,.0f}"
    print(f"{period}\t{fn246}\t{fn247}\t{fn254}\t{fn255}\t{shebao}\t{simu}")
tq.close()
