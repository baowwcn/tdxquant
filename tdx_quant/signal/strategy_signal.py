"""
买卖点信号 - 严格缠论版
"""
from typing import Dict, Any
import pandas as pd
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi import build_strict_bis, get_chan_structure


def generate_signal(df, analysis_result: Dict[str, Any]) -> str:
    """生成交易信号"""
    close = analysis_result.get("close", 0)
    ma5 = analysis_result.get("ma5", 0)
    ma10 = analysis_result.get("ma10", 0)
    ma20 = analysis_result.get("ma20", 0)
    macd_hist = analysis_result.get("macd_hist", 0)
    rsi = analysis_result.get("rsi", 50)
    boll_mid = analysis_result.get("boll_mid", 0)
    boll_down = analysis_result.get("boll_down", 0)

    if close < boll_down:
        return "BUY"
    if rsi < 30:
        return "BUY"
    if macd_hist > 0 and rsi < 70:
        if close > ma5 > ma10 > ma20:
            return "BUY"
    if rsi > 70:
        return "SELL"
    if macd_hist < 0 and rsi > 50:
        if close < ma5:
            return "SELL"
    return "HOLD"


def analyze_chan(kline: pd.DataFrame) -> Dict[str, Any]:
    """缠论分析（严格版）"""
    if kline is None or len(kline) < 20:
        return {"error": "数据不足"}

    fractals, clean_df = detect_fractals(kline)
    bis = build_strict_bis(fractals)

    confirmed = [b for b in bis if b.confirmed]
    unconfirmed = [b for b in bis if not b.confirmed]

    result = {
        "fractal_count": len(fractals),
        "bi_count": len(bis),
        "confirmed_count": len(confirmed),
        "unconfirmed_count": len(unconfirmed),
        "clean_len": len(clean_df),
        "original_len": len(kline),
        "fractals": [f for f in fractals[-10:]],
        "bis": [b for b in bis[-10:]],
        "confirmed_bis": confirmed[-5:] if confirmed else [],
        "last_bi": bis[-1] if bis else None,
        "last_confirmed_bi": confirmed[-1] if confirmed else None,
    }

    return result


def print_chan_signal(kline: pd.DataFrame):
    """打印缠论信号分析"""
    result = analyze_chan(kline)

    if "error" in result:
        print(f"分析失败: {result['error']}")
        return

    print("\n" + "=" * 55)
    print("  缠论结构分析（严格版）")
    print("=" * 55)

    print(f"\nK线: {result['original_len']}根 -> 处理后{result['clean_len']}根")
    print(f"分型: {result['fractal_count']}个")
    print(f"笔: {result['bi_count']}个 (已确认:{result['confirmed_count']} 未确认:{result['unconfirmed_count']})")

    print(f"\n已确认笔 (用于交易决策):")
    for b in result["confirmed_bis"]:
        print(f"  {b}")

    print(f"\n未确认笔:")
    for b in result["bis"][-3:]:
        if not b.confirmed:
            print(f"  {b}")

    if result["last_confirmed_bi"]:
        lb = result["last_confirmed_bi"]
        direction_cn = "上涨" if lb.direction == "up" else "下跌"
        print(f"\n最近已确认笔:")
        print(f"  方向: {direction_cn}")
        print(f"  范围: {lb.start.price:.2f} -> {lb.end.price:.2f}")
        print(f"  幅度: {lb.length:.2f}")

    print("=" * 55)


def get_strict_signal(kline: pd.DataFrame) -> Dict[str, Any]:
    """获取严格版交易信号"""
    result = analyze_chan(kline)

    if "error" in result:
        return result

    signals = []
    reasons = []

    # 只使用已确认笔
    confirmed = result.get("confirmed_bis", [])
    if not confirmed:
        return {"signal": "HOLD", "reason": "无已确认笔"}

    last_confirmed = confirmed[-1]

    # 笔方向
    if last_confirmed.direction == "down":
        signals.append("SELL")
        reasons.append("已确认笔方向下跌")

    # 检查是否有新的未确认反向笔
    if result["last_bi"]:
        current = result["last_bi"]
        if current.direction != last_confirmed.direction:
            signals.append("SELL")
            reasons.append("出现反向未确认笔，可能笔破坏")

    return {
        "signal": signals[0] if signals else "HOLD",
        "reason": reasons if reasons else ["无明确信号"],
        "last_confirmed_bi": last_confirmed,
        "current_bi": result.get("last_bi"),
        "confirmed_count": result["confirmed_count"]
    }