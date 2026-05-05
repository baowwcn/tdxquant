"""
纯缠论分析 - 只看笔结构
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi import build_strict_bis

tq.initialize(__file__)
fetcher = DataFetcher()

# 获取最近数据
df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

print("=" * 60)
print("  纯缠论分析 - 上证指数")
print("=" * 60)

fractals, clean_df = detect_fractals(df)
bis = build_strict_bis(fractals)

confirmed = [b for b in bis if b.confirmed]
unconfirmed = [b for b in bis if not b.confirmed]

print(f"\n【整体笔结构】")
print(f"  总笔数: {len(bis)}")
print(f"  已确认笔: {len(confirmed)}")
print(f"  未确认笔: {len(unconfirmed)}")

# ========== 纯缠论分析 ==========
print(f"\n{'='*60}")
print("  缠论视角分析")
print("="*60)

if len(confirmed) < 2:
    print("  数据不足以做缠论分析")
    tq.close()
    exit()

# 1. 已确认笔方向（这是交易决策依据）
last_confirmed = confirmed[-1]
prev_confirmed = confirmed[-2] if len(confirmed) >= 2 else None

print(f"\n【1. 已确认笔方向（交易依据）】")
dir_cn = "上涨" if last_confirmed.direction == "up" else "下跌"
print(f"  最近已确认笔: {dir_cn}")
print(f"  范围: {last_confirmed.start.price:.2f} -> {last_confirmed.end.price:.2f}")
print(f"  幅度: {last_confirmed.length:.2f} ({last_confirmed.length/last_confirmed.start.price*100:+.2f}%)")

# 2. 笔破坏检测
print(f"\n【2. 笔破坏检测】")
if unconfirmed:
    current = unconfirmed[-1]
    print(f"  当前未确认笔: {'上涨' if current.direction == 'up' else '下跌'}")
    print(f"  范围: {current.start.price:.2f} -> {current.end.price:.2f}")

    # 判断是否笔破坏
    if last_confirmed.direction == "up" and current.direction == "down":
        # 下跌笔是否跌破上涨笔低点
        if current.end.price < last_confirmed.start.price:
            print(f"  WARNING - 笔破坏确认！上涨笔被跌破")
            print(f"  跌破点: {last_confirmed.start.price:.2f}")
            bi_break = True
        else:
            print(f"  笔破坏中，但未有效跌破")
            bi_break = False
    elif last_confirmed.direction == "down" and current.direction == "up":
        # 上涨笔是否突破下跌笔高点
        if current.end.price > last_confirmed.start.price:
            print(f"  WARNING - 笔破坏！下跌笔被突破")
            bi_break = True
        else:
            bi_break = False
    else:
        print(f"  暂无笔破坏")
        bi_break = False
else:
    print(f"  无未确认笔")
    bi_break = False

# 3. 背驰判断（严格缠论）
print(f"\n【3. 背驰判断】")
if len(confirmed) >= 2:
    # 比较最近两个同向已确认笔
    if last_confirmed.direction == prev_confirmed.direction:
        # 计算力度
        curr_strength = last_confirmed.length / (last_confirmed.end_idx - last_confirmed.start_idx)
        prev_strength = prev_confirmed.length / (prev_confirmed.end_idx - prev_confirmed.start_idx)

        print(f"  当前笔力度: {curr_strength:.2f}/K线")
        print(f"  前同向笔力度: {prev_strength:.2f}/K线")

        if last_confirmed.direction == "up":
            if curr_strength < prev_strength * 0.8:
                print(f"  WARNING - 顶背驰！上涨乏力")
                divergence = True
            else:
                print(f"  无背驰")
                divergence = False
        else:
            if curr_strength < prev_strength * 0.8:
                print(f"  WARNING - 底背驰！下跌无力，可能反弹")
                divergence = True
            else:
                print(f"  无背驰")
                divergence = False
    else:
        print(f"  方向不同，无法比较背驰")
        divergence = False
else:
    print(f"  数据不足，无法判断背驰")
    divergence = False

# 4. 笔的新形成
print(f"\n【4. 笔的形成阶段】")
if unconfirmed:
    if unconfirmed[-1].direction == last_confirmed.direction:
        print(f"  当前笔方向与已确认笔一致，延续趋势")
    else:
        print(f"  当前笔方向与已确认笔相反，可能是转折点")

# ========== 纯缠论结论 ==========
print(f"\n{'='*60}")
print("  纯缠论结论")
print("="*60)

# 只基于笔结构判断
if last_confirmed.direction == "down":
    print(f"  WARNING - 已确认笔方向: 下跌")
    print(f"  建议: 不宜买入，等待下跌笔结束")
elif bi_break:
    print(f"  WARNING - 发生笔破坏")
    print(f"  建议: 观望，等待新的笔确认")
elif divergence and last_confirmed.direction == "up":
    print(f"  WARNING - 出现顶背驰")
    print(f"  建议: 减仓/观望")
else:
    if unconfirmed and unconfirmed[-1].direction == "up":
        print(f"  当前形成上涨笔，但未确认")
        print(f"  建议: 等待确认后再操作")
    else:
        print(f"  方向不明，观望为主")

print(f"\n  记住：只用已确认笔做决策，未确认笔会变化")
print("="*60)

tq.close()