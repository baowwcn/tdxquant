"""
宽松版缠论分析 - 基于最近笔
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi import build_strict_bis

tq.initialize(__file__)
fetcher = DataFetcher()

# 获取最近500天数据
df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

print("=" * 60)
print("  宽松版缠论分析 - 上证指数")
print("=" * 60)

print(f"\n数据范围: {str(df.index[0])[:10]} - {str(df.index[-1])[:10]}")

fractals, clean_df = detect_fractals(df)
bis = build_strict_bis(fractals)

print(f"\n笔结构: 共{len(bis)}笔")

# 取最近10笔分析
recent_bis = bis[-10:] if len(bis) >= 10 else bis

print("\n=== 最近10笔 ===")
for i, b in enumerate(recent_bis):
    start_date = df.index[b.start_idx] if b.start_idx < len(df) else "N/A"
    end_date = df.index[b.end_idx] if b.end_idx < len(df) else "N/A"

    start_str = str(start_date)[:10] if isinstance(start_date, str) else str(start_date)[:10]
    end_str = str(end_date)[:10] if isinstance(end_date, str) else str(end_date)[:10]

    dir_cn = "↑上涨" if b.direction == "up" else "↓下跌"
    print(f"  笔{i+1}: {dir_cn}  {start_str} {b.start.price:.2f} -> {end_str} {b.end.price:.2f}")

# 当前最后一笔
current_bi = bis[-1]
print(f"\n=== 当前笔 ===")
print(f"  方向: {'上涨' if current_bi.direction == 'up' else '下跌'}")
print(f"  时间: {str(df.index[current_bi.start_idx])[:10]} -> {str(df.index[current_bi.end_idx])[:10]}")
print(f"  价格: {current_bi.start.price:.2f} -> {current_bi.end.price:.2f}")
print(f"  幅度: {current_bi.length:.2f} ({current_bi.length/current_bi.start.price*100:+.2f}%)")

# 判断当前笔是否完成
print(f"\n=== 当前笔状态 ===")
current_end_date = df.index[current_bi.end_idx]
data_end_date = df.index[-1]

if str(current_end_date)[:10] == str(data_end_date)[:10]:
    print(f"  状态: 正在形成中（今天刚形成）")
else:
    days_since = (data_end_date - current_end_date).days
    print(f"  状态: 已形成 {days_since} 个交易日")

# 前面一笔
if len(bis) >= 2:
    prev_bi = bis[-2]
    print(f"\n=== 前一笔 ===")
    print(f"  方向: {'上涨' if prev_bi.direction == 'up' else '下跌'}")
    print(f"  价格: {prev_bi.start.price:.2f} -> {prev_bi.end.price:.2f}")

    # 笔破坏判断
    if current_bi.direction != prev_bi.direction:
        if current_bi.direction == "up":
            # 上涨笔突破前低？
            if current_bi.end.price > prev_bi.start.price:
                print(f"  笔破坏: YES - 上涨笔突破前高点")
                bi_break = True
            else:
                print(f"  笔破坏: 未有效突破")
                bi_break = False
        else:
            # 下跌笔跌破前低？
            if current_bi.end.price < prev_bi.start.price:
                print(f"  笔破坏: YES - 下跌笔跌破前低点")
                bi_break = True
            else:
                print(f"  笔破坏: 未有效跌破")
                bi_break = False

        direction_changed = True
    else:
        print(f"  笔破坏: 同向延续")
        bi_break = False
        direction_changed = False
else:
    bi_break = False
    direction_changed = False

# 背驰判断（同向笔比较）
print(f"\n=== 背驰分析 ===")
same_dir_bis = [b for b in recent_bis if b.direction == current_bi.direction]
if len(same_dir_bis) >= 2:
    curr = same_dir_bis[-1]
    prev = same_dir_bis[-2]

    curr_len = curr.length / (curr.end_idx - curr.start_idx)
    prev_len = prev.length / (prev.end_idx - prev.start_idx)

    print(f"  当前同向笔力度: {curr_len:.2f}/K线")
    print(f"  前同向笔力度: {prev_len:.2f}/K线")

    if curr_len < prev_len * 0.8:
        if current_bi.direction == "up":
            print(f"  结论: WARNING - 顶背驰！上涨乏力")
        else:
            print(f"  结论: 底背驰！下跌无力，可能反弹")
        divergence = True
    else:
        print(f"  结论: 无背驰")
        divergence = False
else:
    print(f"  数据不足，无法判断")
    divergence = False

# 宽松版结论（使用最近笔）
print(f"\n{'='*60}")
print("  宽松版缠论结论（基于最近笔）")
print("="*60)

if current_bi.direction == "up":
    print(f"  当前笔方向: 上涨")
    if bi_break:
        print(f"  状态: 笔破坏，新趋势形成中")
    if divergence:
        print(f"  警告: 可能背驰")
    print(f"  建议: 可关注，但需等回调确认")
else:
    print(f"  当前笔方向: 下跌")
    if divergence:
        print(f"  注意: 底背驰，可能见底反弹")
    print(f"  建议: 等待下跌笔结束")

# 根据当前情况给建议
if current_bi.direction == "up" and not bi_break and not divergence:
    print(f"\n  综上: 上涨笔延续中，可适当关注")
elif current_bi.direction == "up" and bi_break:
    print(f"\n  综上: 刚经历笔破坏，方向不明，观望为主")
elif current_bi.direction == "down":
    print(f"\n  综上: 下跌笔中，不宜买入")

print("="*60)

tq.close()