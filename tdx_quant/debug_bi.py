import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi import clean_fractals, build_strict_bis

tq.initialize(__file__)
fetcher = DataFetcher()

# 获取所有数据
df = fetcher.get_kline(code="000001.SH", period="1d", count=1000)

fractals, clean_df = detect_fractals(df)
bis = build_strict_bis(fractals)

print(f"总K线: {len(df)} 根")
print(f"日期范围: {str(df.index[0])[:10]} - {str(df.index[-1])[:10]}")
print(f"分型数: {len(fractals)}")
print(f"总笔数: {len(bis)}")

print("\n=== 所有笔（按时间顺序）===")
for i, b in enumerate(bis):
    # 获取该笔对应的时间
    start_date = df.index[b.start_idx] if b.start_idx < len(df) else "N/A"
    end_date = df.index[b.end_idx] if b.end_idx < len(df) else "N/A"

    dir_cn = "↑" if b.direction == "up" else "↓"
    status = "OK" if b.confirmed else "..."

    start_str = str(start_date)[:10] if start_date != "N/A" else str(b.start_idx)
    end_str = str(end_date)[:10] if end_date != "N/A" else str(b.end_idx)

    print(f"笔{i+1}: {dir_cn} {status}  {start_str} {b.start.price:.2f} -> {end_str} {b.end.price:.2f}")

tq.close()