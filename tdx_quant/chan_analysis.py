"""
缠论买卖点分析
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
import pandas as pd
from tdx_quant.signal.fractal import detect_fractals, merge_included_bars
from tdx_quant.signal.bi import build_bis


def analyze_buy_sell(df: pd.DataFrame) -> dict:
    """缠论买卖点分析"""

    merged = merge_included_bars(df)
    fractals = detect_fractals(merged)
    bis = build_bis(fractals)

    if not bis:
        return {"signal": "HOLD", "reason": "数据不足"}

    last_bi = bis[-1]

    close = df["close"].iloc[-1]
    open_price = df["open"].iloc[-1]
    high = df["high"].iloc[-1]
    low = df["low"].iloc[-1]

    # 获取最近几笔
    recent_bis = bis[-5:] if len(bis) >= 5 else bis

    # 计算笔力度
    bi_angles = []
    for b in recent_bis:
        angle = (b.end.price - b.start.price) / (b.end_idx - b.start_idx)
        bi_angles.append({
            "direction": b.direction,
            "angle": angle,
            "start": b.start.price,
            "end": b.end.price
        })

    # 判断逻辑
    signal = "HOLD"
    reason = []

    # 1. 当前笔方向
    if last_bi.direction == "up":
        # 上涨笔：检查是否出现背驰或回调

        # 计算涨幅
        bi_length = last_bi.end.price - last_bi.start.price
        bi_pct = bi_length / last_bi.start.price * 100

        if bi_pct > 8:
            reason.append(f"当前上涨笔涨幅{bi_pct:.1f}%较大")

        # 检查前一笔力度（背驰判断）
        if len(recent_bis) >= 2:
            prev_bi = recent_bis[-2]
            if prev_bi.direction == "up":
                prev_angle = (prev_bi.end.price - prev_bi.start.price) / (prev_bi.end_idx - prev_bi.start_idx)
                curr_angle = (last_bi.end.price - last_bi.start.price) / (last_bi.end_idx - last_bi.start_idx)

                if curr_angle < prev_angle * 0.8:
                    signal = "SELL"
                    reason.append("上涨力度减弱，出现背驰")

        # 检查是否开始回调（形成笔破坏）
        # 笔破坏：下跌笔突破前一笔的低点
        if low < last_bi.low:
            signal = "SELL"
            reason.append("笔破坏：跌破上涨笔低点")

    else:
        # 下跌笔：可能形成底分型
        bi_length = last_bi.start.price - last_bi.end.price
        bi_pct = bi_length / last_bi.start.price * 100

        if bi_pct > 5:
            reason.append(f"当前下跌笔跌幅{bi_pct:.1f}%")

        # 检查是否形成底分型
        if len(fractals) >= 2:
            last_frac = fractals[-1]
            if last_frac.ftype == "bottom":
                if close > open_price:
                    signal = "BUY"
                    reason.append("底分型+阳线")

    # 默认判断
    if signal == "HOLD":
        if last_bi.direction == "up":
            # 检查回调力度
            recent_low = df["low"].iloc[-5:].min()
            if close > last_bi.start.price * 1.05:
                signal = "HOLD"
                reason.append("上涨笔持续中，未出现明显回调")

                # RSI判断
                if len(df) >= 14:
                    rsi = 100 - (100 / (1 + (df["close"].diff().apply(lambda x: max(x, 0)).rolling(14).mean() /
                                    df["close"].diff().apply(lambda x: abs(min(x, 0))).rolling(14).mean()).iloc[-1]))
                    if rsi and rsi > 80:
                        signal = "SELL"
                        reason.append(f"RSI超买({rsi:.0f})")
        else:
            signal = "BUY"
            reason.append("下跌笔结束，关注反弹")

    return {
        "signal": signal,
        "reason": reason,
        "current_bi": last_bi,
        "bi_direction": last_bi.direction,
        "bi_pct": (last_bi.end.price - last_bi.start.price) / last_bi.start.price * 100 if last_bi.direction == "up" else (last_bi.start.price - last_bi.end.price) / last_bi.start.price * 100,
        "recent_bis": bi_angles
    }


tq.initialize(__file__)

from tdx_quant.data.fetcher import DataFetcher
fetcher = DataFetcher()
df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

if df is not None:
    result = analyze_buy_sell(df)

    print("=" * 60)
    print("  缠论买卖点分析 - 上证指数")
    print("=" * 60)
    print(f"\n当前信号: {result['signal']}")

    print(f"\n当前笔方向: {'上涨' if result['bi_direction'] == 'up' else '下跌'}")
    print(f"当前笔幅度: {result['bi_pct']:.2f}%")

    print(f"\n分析理由:")
    for r in result["reason"]:
        print(f"  - {r}")

    print("\n最近5笔力度:")
    for i, ba in enumerate(result["recent_bis"]):
        direction = "↑" if ba["direction"] == "up" else "↓"
        print(f"  {i+1}. {direction} 幅度:{ba['end']-ba['start']:.2f}")

    # 综合判断
    print("\n" + "=" * 60)
    print("  综合判断")
    print("=" * 60)

    if result["signal"] == "BUY":
        print("  建议: 关注买入机会")
        print("  理由: 下跌笔结束，可能形成底部")
    elif result["signal"] == "SELL":
        print("  建议: 谨慎/卖出")
        print("  理由: 上涨笔出现背驰或笔破坏，注意风险")
    else:
        print("  建议: 持有观望")
        print("  理由: 上涨笔持续中，但需关注回调风险")
        print("  ⚠️ 风险提示: RSI超买，注意短期回调")

    print("=" * 60)

tq.close()