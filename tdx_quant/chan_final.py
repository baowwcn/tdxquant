"""
宽松版缠论分析 - 基于最新数据
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi_simple import build_simple_bis, clean_fractals_simple

tq.initialize(__file__)
fetcher = DataFetcher()

# 获取最近200天数据（足够分析近期结构）
df = fetcher.get_kline(code="000001.SH", period="1d", count=200)

print("=" * 60)
print("  宽松版缠论分析 - 上证指数")
print("=" * 60)

print(f"\n数据范围: {str(df.index[0])[:10]} - {str(df.index[-1])[:10]}")
print(f"共 {len(df)} 个交易日")

# 获取分型和笔
fractals, clean_df = detect_fractals(df)
bis = build_simple_bis(fractals)

print(f"\n笔结构: 共 {len(bis)} 笔")

# 打印最近15笔（带日期）
print("\n=== 最近15笔 ===")
recent_bis = bis[-15:] if len(bis) >= 15 else bis

for i, b in enumerate(recent_bis):
    try:
        start_date = df.index[b.start_idx] if b.start_idx < len(df) else "N/A"
        end_date = df.index[b.end_idx] if b.end_idx < len(df) else "N/A"
        start_str = str(start_date)[:10] if start_date != "N/A" else str(b.start_idx)
        end_str = str(end_date)[:10] if end_date != "N/A" else str(b.end_idx)
    except:
        start_str = str(b.start_idx)
        end_str = str(b.end_idx)

    dir_cn = "↑上涨" if b.direction == "up" else "↓下跌"
    print(f"  笔{i+1}: {dir_cn}  {start_str} {b.start_price:.2f} -> {end_str} {b.end_price:.2f}")

# 当前笔分析
current_bi = bis[-1]
print(f"\n{'='*60}")
print("  当前笔分析")
print("="*60)

try:
    start_date = df.index[current_bi.start_idx]
    end_date = df.index[current_bi.end_idx]
    start_str = str(start_date)[:10]
    end_str = str(end_date)[:10]
except:
    start_str = str(current_bi.start_idx)
    end_str = str(current_bi.end_idx)

print(f"  当前笔方向: {'上涨' if current_bi.direction == 'up' else '下跌'}")
print(f"  笔时间: {start_str} -> {end_str}")
print(f"  价格: {current_bi.start_price:.2f} -> {current_bi.end_price:.2f}")
print(f"  幅度: {current_bi.length:.2f} ({current_bi.length/current_bi.start_price*100:+.2f}%)")

# 笔破坏检测
print(f"\n{'='*60}")
print("  笔破坏与背驰分析")
print("="*60)

if len(bis) >= 2:
    prev_bi = bis[-2]

    # 笔破坏判断
    if current_bi.direction != prev_bi.direction:
        if current_bi.direction == "up":
            if current_bi.end_price > prev_bi.start_price:
                print(f"  笔破坏: YES - 上涨笔突破前高({prev_bi.start_price:.2f})")
                bi_break = True
            else:
                print(f"  笔破坏: NO - 上涨笔未突破前高")
                bi_break = False
        else:
            if current_bi.end_price < prev_bi.start_price:
                print(f"  笔破坏: YES - 下跌笔跌破前低({prev_bi.start_price:.2f})")
                bi_break = True
            else:
                print(f"  笔破坏: NO - 下跌笔未跌破前低")
                bi_break = False

        print(f"  趋势转折: YES - 笔方向改变")
        direction_changed = True
    else:
        print(f"  笔破坏: NO - 同方向延续")
        bi_break = False
        direction_changed = False
        print(f"  趋势: 延续中")

    # 背驰判断（比较同向笔力度）
    same_dir = [b for b in bis[-5:] if b.direction == current_bi.direction]
    if len(same_dir) >= 2:
        curr = same_dir[-1]
        prev = same_dir[-2]

        curr_strength = curr.length / (curr.end_idx - curr.start_idx + 1)
        prev_strength = prev.length / (prev.end_idx - prev.start_idx + 1)

        print(f"\n  背驰分析:")
        print(f"    当前同向笔力度: {curr_strength:.2f}/K线")
        print(f"    前同向笔力度: {prev_strength:.2f}/K线")

        if curr_strength < prev_strength * 0.7:
            if current_bi.direction == "up":
                print(f"    结论: WARNING - 顶背驰！上涨乏力")
            else:
                print(f"    结论: 底背驰！下跌无力，可能反弹")
            divergence = True
        else:
            print(f"    结论: 无背驰")
            divergence = False
    else:
        divergence = False

else:
    bi_break = False
    direction_changed = False
    divergence = False

# 当前价格位置
current_price = df["close"].iloc[-1]
print(f"\n{'='*60}")
print("  当前价格位置")
print("="*60)

print(f"  当前收盘: {current_price:.2f}")
print(f"  当前笔起点: {current_bi.start_price:.2f}")
print(f"  当前笔终点: {current_bi.end_price:.2f}")

if current_bi.direction == "up":
    if current_price > current_bi.end_price:
        print(f"  价格已突破当前笔终点，趋势延续")
    elif current_price > current_bi.start_price:
        pct = (current_price - current_bi.start_price) / (current_bi.end_price - current_bi.start_price) * 100
        print(f"  价格在当前笔区间内: {pct:.1f}% 位置")
else:
    if current_price < current_bi.end_price:
        print(f"  价格已跌破当前笔终点，新低出现")
    elif current_price < current_bi.start_price:
        pct = (current_bi.start_price - current_price) / (current_bi.start_price - current_bi.end_price) * 100
        print(f"  价格在当前笔区间内: {pct:.1f}% 位置")

# 宽松版最终结论
print(f"\n{'='*60}")
print("  宽松版缠论结论")
print("="*60)

if current_bi.direction == "up":
    if bi_break and direction_changed:
        print(f"  当前状态: 笔破坏后，新上涨趋势形成中")
        print(f"  建议: 关注回调买入机会")
    elif divergence:
        print(f"  当前状态: 上涨笔，但出现背驰")
        print(f"  建议: 谨慎，可能回调")
    else:
        print(f"  当前状态: 上涨笔延续中")
        print(f"  建议: 顺势而为，但注意风险")
else:
    if divergence:
        print(f"  当前状态: 下跌笔，但出现底背驰")
        print(f"  建议: 关注反弹机会")
    else:
        print(f"  当前状态: 下跌笔")
        print(f"  建议: 不宜买入，等待止跌")

# 实际操作建议
print(f"\n  实际操作建议:")
if current_bi.direction == "up" and not divergence:
    print(f"    - 短期偏多，可考虑回调买入")
    print(f"    - 止损位: {current_bi.start_price:.2f}")
elif current_bi.direction == "up" and (bi_break or divergence):
    print(f"    - 建议观望或轻仓")
    print(f"    - 等待方向明确")
else:
    print(f"    - 建议等待，不宜买入")

print("="*60)

tq.close()