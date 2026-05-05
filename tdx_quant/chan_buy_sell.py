"""
缠论买卖点分析 - 标准版
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
import pandas as pd
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi import build_bis


tq.initialize(__file__)

from tdx_quant.data.fetcher import DataFetcher
fetcher = DataFetcher()
df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

if df is None:
    print("数据获取失败")
    tq.close()
    exit()

fractals, clean_df = detect_fractals(df)
bis = build_bis(fractals)

print("=" * 60)
print("  缠论买卖点分析 - 上证指数")
print("=" * 60)

if len(bis) < 2:
    print("数据不足")
    tq.close()
    exit()

# 最近5笔
recent_bis = bis[-6:] if len(bis) >= 6 else bis

print(f"\n【最近笔走势】")
for i, b in enumerate(recent_bis):
    direction = "↑" if b.direction == "up" else "↓"
    change = b.length if b.direction == "up" else -b.length
    print(f"  笔{i+1}: {direction} {b.start.price:.2f} → {b.end.price:.2f} (变化: {change:+.2f})")

# 当前笔
current_bi = bis[-1]
prev_bi = bis[-2] if len(bis) >= 2 else None

print(f"\n【当前状态】")
print(f"  当前笔方向: {'上涨' if current_bi.direction == 'up' else '下跌'}")
print(f"  当前笔: {current_bi.start.price:.2f} → {current_bi.end.price:.2f}")
print(f"  当前笔变化: {current_bi.length:+.2f}")

# 背驰判断
print(f"\n【背驰分析】")
if prev_bi and current_bi.direction == "up" and prev_bi.direction == "up":
    curr_strength = current_bi.length / (current_bi.end_idx - current_bi.start_idx)
    prev_strength = prev_bi.length / (prev_bi.end_idx - prev_bi.start_idx)
    print(f"  当前笔力度: {curr_strength:.2f}/K线")
    print(f"  前笔力度: {prev_strength:.2f}/K线")
    if curr_strength < prev_strength * 0.8:
        print(f"  WARNING - 背驰确认！上涨力度减弱")
        has_divergence = True
    else:
        print(f"  暂无背驰")
        has_divergence = False
else:
    print(f"  方向不一致，无法比较")
    has_divergence = False

# 技术指标
close = df["close"].iloc[-1]
open_price = df["open"].iloc[-1]
high = df["high"].iloc[-1]
low = df["low"].iloc[-1]

print(f"\n【技术指标】")
print(f"  收盘: {close:.2f}")
print(f"  涨跌: {(close - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100:+.2f}%")

# RSI
delta = df["close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs)).iloc[-1]
print(f"  RSI(14): {rsi:.1f}")

# 判断
print(f"\n" + "=" * 60)
print("  综合判断")
print("=" * 60)

signals = []
reasons = []

# 1. 笔方向判断
if current_bi.direction == "down":
    signals.append("SELL")
    reasons.append("当前处于下跌笔")

# 2. 笔破坏判断
if prev_bi and prev_bi.direction == "up" and current_bi.direction == "down":
    signals.append("SELL")
    reasons.append("笔破坏：上涨笔被下跌笔打破")

# 3. 背驰
if has_divergence:
    signals.append("SELL")
    reasons.append("上涨背驰")

# 4. RSI
if rsi > 75:
    signals.append("SELL")
    reasons.append(f"RSI超买({rsi:.0f})")
elif rsi < 30:
    signals.append("BUY")
    reasons.append(f"RSI超卖({rsi:.0f})")

# 5. 笔幅度
if current_bi.direction == "up":
    pct = current_bi.length / current_bi.start.price * 100
    if pct > 15:
        signals.append("SELL")
        reasons.append(f"上涨笔幅度过大({pct:.1f}%)")

# 决策
if "SELL" in signals:
    recommendation = "WARNING - 不建议买入"
    action = "观望/减仓"
elif "BUY" in signals:
    recommendation = "OK - 关注买入"
    action = "准备建仓"
else:
    recommendation = "HOLD - 持有观望"
    action = "等待方向明确"

print(f"\n  建议: {recommendation}")
print(f"  操作: {action}")

print(f"\n  理由:")
for r in reasons:
    print(f"    - {r}")

if not reasons:
    print(f"    - 当前无明显信号")

print(f"\n  风险提示:")
if rsi > 70:
    print(f"    WARNING - RSI超买，短期有回调风险")
if current_bi.direction == "down":
    print(f"    WARNING - 下跌笔中，建议等待止跌")

print("=" * 60)

tq.close()