import sys, io, re, csv, datetime

sys.path.insert(0, "C:/new_tdx64/PYPlugins/user")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from urllib.request import urlopen

ETF_CODE = "515220.SH"
ETF_NAME = "煤炭ETF国泰"
FUND_ID = "515220"

MODE = "holdings"
if len(sys.argv) > 1 and sys.argv[1] in ("--holder", "-r"):
    MODE = "holder"


def fetch_holdings():
    from tqcenter import tq

    tq.initialize("dummy.py")

    print(f"{ETF_NAME} ({ETF_CODE}) 持仓查询\n{'-' * 60}")
    url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={FUND_ID}&topline=100&year=2026&month="
    print("1. 从天天基金获取最新持仓...")
    with urlopen(url, timeout=15) as resp:
        html = resp.read().decode("utf-8")

    code_matches = re.findall(r"href='[^']*?/(\d)\.(\d{6})'>\2</a>", html)
    name_matches = re.findall(
        r"'>(\d{6})</a></td><td class='tol'><a[^>]*>([^<]+)</a>", html
    )
    pct_matches = re.findall(r"<td class='tor'>([\d.]+)%</td>", html)

    holdings = []
    for i, (market_flag, code) in enumerate(code_matches):
        name = ""
        for cm, nm in name_matches:
            if cm == code:
                name = nm
                break
        pct = pct_matches[i] if i < len(pct_matches) else "--"
        if market_flag == "1":
            full_code = f"{code}.SH"
        elif market_flag == "0":
            full_code = f"{code}.SZ"
        else:
            full_code = code
        holdings.append({"code": full_code, "name": name, "pct": pct})

    print(f"  获取到 {len(holdings)} 只持仓股票 (截至2026Q1)\n")
    print("2. 获取通达信实时行情数据...")
    for i, h in enumerate(holdings):
        more = tq.get_more_info(h["code"], ["Zsz", "Ltsz", "ZAF", "DynaPE", "fHSL"])
        h["zsz"] = more.get("Zsz", "--")
        h["zaf"] = more.get("ZAF", "--")
        h["pe"] = more.get("DynaPE", "--")
        h["hsl"] = more.get("fHSL", "--")
        snap = tq.get_market_snapshot(h["code"])
        h["now"] = snap.get("Now", "--") if snap else "--"
        if (i + 1) % 10 == 0:
            print(f"  已处理 {i + 1}/{len(holdings)}...")

    print(f"\n{'=' * 100}")
    print(f"{ETF_NAME} ({ETF_CODE}) 重仓成分股")
    print(f"{'=' * 100}")
    print(
        f"{'#':<4} {'代码':<14} {'名称':<10} {'占净值%':<10} {'最新价':<10} {'总市值(亿)':<12} {'涨幅%':<8} {'市盈率':<8} {'换手%':<8}"
    )
    print("-" * 88)
    for i, h in enumerate(holdings):
        zsz = f"{float(h['zsz']):.1f}" if h["zsz"] not in ("--", None, "") else "--"
        zaf = f"{float(h['zaf']):.2f}" if h["zaf"] not in ("--", None, "") else "--"
        pe = f"{float(h['pe']):.1f}" if h["pe"] not in ("--", None, "") else "--"
        hsl = f"{float(h['hsl']):.2f}" if h["hsl"] not in ("--", None, "") else "--"
        print(
            f"{i + 1:<4} {h['code']:<14} {h['name']:<9} {str(h['pct']):<10} {str(h['now']):<10} {zsz:<12} {zaf:<8} {pe:<8} {hsl:<8}"
        )

    total_pct = sum(
        float(h["pct"]) for h in holdings if h["pct"] not in ("--", None, "")
    )
    top10_pct = sum(
        float(h["pct"]) for h in holdings[:10] if h["pct"] not in ("--", None, "")
    )
    sh = [h for h in holdings if h["code"].endswith(".SH")]
    sz = [h for h in holdings if h["code"].endswith(".SZ")]
    kechuang = [h for h in holdings if h["code"].startswith("688")]

    print(f"\n持仓汇总:")
    print(f"  披露持仓数量: {len(holdings)} 只")
    print(f"  前10大重仓股占比: {top10_pct:.2f}%")
    print(f"  披露持仓占净值比例: {total_pct:.2f}%")
    print(f"  沪市(含科创板): {len(sh)} 只 | 深市(含创业板): {len(sz)} 只")
    print(f"  科创板股票: {len(kechuang)} 只")
    tq.close()


def fetch_holder():
    date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}")
    print(f"{ETF_NAME} ({ETF_CODE}) 持有人结构\n{'-' * 60}")
    for year in range(2027, 2018, -1):
        url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=cyrjg&code={FUND_ID}&year={year}"
        try:
            with urlopen(url, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
        except:
            continue
        m = re.search(r'content:"(.+?)"\)', raw)
        html = m.group(1).replace(r"\"", '"').replace(r"\/", "/") if m else raw
        rows = re.findall(
            r"<tr><td>(\d{4}-\d{2}-\d{2})</td><td[^>]*>([^<]+)%</td>"
            r"<td[^>]*>([^<]+)%</td><td[^>]*>([^<]+)%</td><td[^>]*>([^<]+)</td></tr>",
            html,
        )
        if not rows:
            continue
        print(
            f"{'公告日期':<14} {'机构%':>8} {'个人%':>8} {'内部%':>8} {'总份额(亿)':>12}"
        )
        print("-" * 54)
        for r in rows:
            print(f"{r[0]:<14} {r[1]:>8} {r[2]:>8} {r[3]:>8} {r[4]:>12}")
        today = datetime.date.today().strftime("%Y%m%d")
        csv_file = f"{ETF_CODE}_holder_{today}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "公告日期",
                    "机构持有比例",
                    "个人持有比例",
                    "内部持有比例",
                    "总份额(亿份)",
                ]
            )
            w.writerows(rows)
        print(f"\n已保存到: {csv_file}")
        return


if MODE == "holder":
    fetch_holder()
else:
    fetch_holdings()
