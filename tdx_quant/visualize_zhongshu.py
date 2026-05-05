"""
缠论可视化 - K线+分型+笔+中枢
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi_simple import build_simple_bis
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.collections import PatchCollection
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def find_zhongshu(bis):
    """找出笔中枢（至少三笔重叠区域）"""
    if len(bis) < 3:
        return []

    zhongshus = []

    # 至少需要3笔才能形成中枢
    for i in range(len(bis) - 2):
        b1 = bis[i]
        b2 = bis[i + 1]
        b3 = bis[i + 2]

        # 三笔有重叠
        high = min(b1.high, b2.high, b3.high)
        low = max(b1.low, b2.low, b3.low)

        if high > low:  # 有重叠区域
            # 检查方向：中枢方向取决于第一笔和第三笔
            if b1.direction == b3.direction:
                direction = b1.direction
            else:
                direction = "sideways"

            zhongshus.append({
                "start_idx": b1.start_idx,
                "end_idx": b3.end_idx,
                "high": high,
                "low": low,
                "direction": direction,
                "strength": high - low
            })

    return zhongshus


tq.initialize(__file__)
fetcher = DataFetcher()

df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

print(f"数据: {str(df.index[0])[:10]} - {str(df.index[-1])[:10]}")

fractals, clean_df = detect_fractals(df)
bis = build_simple_bis(fractals)
zhongshus = find_zhongshu(bis)

print(f"分型: {len(fractals)}个, 笔: {len(bis)}个, 中枢: {len(zhongshus)}个")

fig = plt.figure(figsize=(18, 12))

# 主图
ax1 = fig.add_subplot(3, 1, 1)

dates = mdates.date2num(df.index.to_pydatetime())
opens = df['open'].values
closes = df['close'].values
highs = df['high'].values
lows = df['low'].values

# K线
width = 0.6
for i in range(len(df)):
    color = 'red' if closes[i] >= opens[i] else 'green'
    height = abs(closes[i] - opens[i])
    bottom = min(opens[i], closes[i])
    rect = Rectangle((dates[i] - width/2, bottom), width, height,
                     facecolor=color, edgecolor=color, alpha=0.8)
    ax1.add_patch(rect)
    ax1.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=0.5)

# 笔
colors_bi = {'up': 'blue', 'down': 'orange'}
for b in bis:
    start_date = df.index[b.start_idx] if b.start_idx < len(df) else df.index[0]
    end_date = df.index[b.end_idx] if b.end_idx < len(df) else df.index[-1]
    start_num = mdates.date2num(start_date.to_pydatetime())
    end_num = mdates.date2num(end_date.to_pydatetime())
    color = colors_bi[b.direction]
    ax1.plot([start_num, end_num], [b.start_price, b.end_price],
             color=color, linewidth=2, alpha=0.7)
    mid = (start_num + end_num) / 2
    mid_price = (b.start_price + b.end_price) / 2
    arrow = '▲' if b.direction == 'up' else '▼'
    ax1.annotate(arrow, (mid, mid_price), fontsize=7, ha='center', color=color, alpha=0.8)

# 中枢（矩形框）
for z in zhongshus[-10:]:  # 只画最近10个中枢
    start_date = df.index[z["start_idx"]] if z["start_idx"] < len(df) else df.index[0]
    end_date = df.index[z["end_idx"]] if z["end_idx"] < len(df) else df.index[-1]
    start_num = mdates.date2num(start_date.to_pydatetime())
    end_num = mdates.date2num(end_date.to_pydatetime())

    rect = FancyBboxPatch((start_num, z["low"]), end_num - start_num, z["high"] - z["low"],
                          boxstyle="round,pad=0.02,rounding_size=0.1",
                          facecolor='yellow', alpha=0.3, edgecolor='purple', linewidth=2)
    ax1.add_patch(rect)

# 分型
for f in fractals:
    if f.index < len(df):
        date = mdates.date2num(df.index[f.index].to_pydatetime())
        if f.ftype == 'top':
            ax1.plot(date, f.price, '^', color='red', markersize=6, alpha=0.5)
        else:
            ax1.plot(date, f.price, 'v', color='green', markersize=6, alpha=0.5)

current_price = closes[-1]
ax1.axhline(y=current_price, color='purple', linestyle='--', alpha=0.5, label=f'Current: {current_price:.2f}')

ax1.set_title('Shanghai Index (000001.SH) - Chan Theory with Zhongshu (中枢)\n2 Years Data', fontsize=14)
ax1.set_ylabel('Price', fontsize=12)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper left')

# 中枢详情图
ax2 = fig.add_subplot(3, 1, 2)

# 笔收益
bi_returns = []
for b in bis:
    ret = (b.end_price - b.start_price) / b.start_price * 100
    bi_returns.append(ret)

colors_ret = ['red' if r > 0 else 'green' for r in bi_returns]
ax2.bar(range(len(bi_returns)), bi_returns, color=colors_ret, alpha=0.7)
ax2.axhline(y=0, color='black', linewidth=0.5)
ax2.set_title('Bi Returns (%)', fontsize=12)
ax2.set_ylabel('Return (%)', fontsize=10)
ax2.grid(True, alpha=0.3)

# 中枢区间图
ax3 = fig.add_subplot(3, 1, 3)

# 画出最近20笔的中枢范围
recent_zs = zhongshus[-15:] if len(zhongshus) >= 15 else zhongshus
y_positions = range(len(recent_zs))

for i, z in enumerate(recent_zs):
    # 中枢区间
    ax3.barh(i, z["high"] - z["low"], left=z["low"], height=0.6,
             color='yellow', alpha=0.5, edgecolor='purple')

    # 标注
    ax3.text(z["high"] + 5, i, f'{z["high"]:.0f}', va='center', fontsize=8)
    ax3.text(z["low"] - 5, i, f'{z["low"]:.0f}', va='center', fontsize=8)

ax3.set_yticks(y_positions)
ax3.set_yticklabels([f'ZS{i+1}' for i in range(len(recent_zs))])
ax3.set_title('Zhongshu (中枢) Ranges - Recent 15', fontsize=12)
ax3.set_xlabel('Price', fontsize=10)
ax3.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('D:\\new_tdx_mock\\PYPlugins\\user\\tdx_quant\\chan_with_zhongshu.png', dpi=150, bbox_inches='tight')
print("\n图片已保存: D:\\new_tdx_mock\\PYPlugins\\user\\tdx_quant\\chan_with_zhongshu.png")

plt.close('all')

# 打印中枢信息
print("\n" + "="*60)
print("  中枢分析")
print("="*60)

if zhongshus:
    print(f"  共识别 {len(zhongshus)} 个中枢")

    # 最近5个中枢
    recent_zs = zhongshus[-5:]
    print(f"\n  最近5个中枢:")
    for i, z in enumerate(recent_zs):
        start_date = df.index[z["start_idx"]] if z["start_idx"] < len(df) else "N/A"
        end_date = df.index[z["end_idx"]] if z["end_idx"] < len(df) else "N/A"
        s = str(start_date)[:10] if start_date != "N/A" else "N/A"
        e = str(end_date)[:10] if end_date != "N/A" else "N/A"

        dir_cn = "上涨" if z["direction"] == "up" else ("下跌" if z["direction"] == "down" else "震荡")

        print(f"    中枢{i+1}: {s} -> {e}")
        print(f"          区间: {z['low']:.2f} - {z['high']:.2f} (振幅:{z['strength']:.2f})")
        print(f"          方向: {dir_cn}")

    # 当前价格与最近中枢的关系
    current = closes[-1]
    if recent_zs:
        last_zs = recent_zs[-1]
        if last_zs["low"] <= current <= last_zs["high"]:
            print(f"\n  当前价格 {current:.2f} 位于最近中枢区间内")
        elif current > last_zs["high"]:
            print(f"\n  当前价格 {current:.2f} 突破最近中枢上沿 {last_zs['high']:.2f}")
        else:
            print(f"\n  当前价格 {current:.2f} 跌破最近中枢下沿 {last_zs['low']:.2f}")

print("="*60)

tq.close()