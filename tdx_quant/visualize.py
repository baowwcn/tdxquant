"""
缠论可视化 - K线+分型+笔
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi_simple import build_simple_bis
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

tq.initialize(__file__)
fetcher = DataFetcher()

# 获取2年数据（约500个交易日）
df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

print(f"数据: {str(df.index[0])[:10]} - {str(df.index[-1])[:10]}")

# 缠论分析
fractals, clean_df = detect_fractals(df)
bis = build_simple_bis(fractals)

print(f"分型: {len(fractals)}个, 笔: {len(bis)}个")

# 创建图形
fig = plt.figure(figsize=(16, 10))

# 主图：K线
ax1 = fig.add_subplot(2, 1, 1)

# 绘制K线
dates = mdates.date2num(df.index.to_pydatetime())
opens = df['open'].values
closes = df['close'].values
highs = df['high'].values
lows = df['low'].values

# K线柱状图
width = 0.6
for i in range(len(df)):
    color = 'red' if closes[i] >= opens[i] else 'green'
    height = abs(closes[i] - opens[i])
    bottom = min(opens[i], closes[i])

    rect = Rectangle((dates[i] - width/2, bottom), width, height,
                     facecolor=color, edgecolor=color, alpha=0.8)
    ax1.add_patch(rect)

    # 上下影线
    ax1.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=0.5)

# 绘制笔
colors = {'up': 'blue', 'down': 'orange'}
for i, b in enumerate(bis):
    start_date = df.index[b.start_idx] if b.start_idx < len(df) else df.index[0]
    end_date = df.index[b.end_idx] if b.end_idx < len(df) else df.index[-1]

    start_num = mdates.date2num(start_date.to_pydatetime())
    end_num = mdates.date2num(end_date.to_pydatetime())

    color = colors[b.direction]
    ax1.plot([start_num, end_num], [b.start_price, b.end_price],
             color=color, linewidth=2, alpha=0.7)

    # 标注方向
    mid = (start_num + end_num) / 2
    mid_price = (b.start_price + b.end_price) / 2
    arrow = '▲' if b.direction == 'up' else '▼'
    ax1.annotate(arrow, (mid, mid_price), fontsize=8, ha='center',
                color=color, alpha=0.8)

# 绘制分型
top_fracs = [f for f in fractals if f.ftype == 'top']
bottom_fracs = [f for f in fractals if f.ftype == 'bottom']

for f in top_fracs:
    if f.index < len(df):
        date = mdates.date2num(df.index[f.index].to_pydatetime())
        ax1.plot(date, f.price, '^', color='red', markersize=8, alpha=0.6)

for f in bottom_fracs:
    if f.index < len(df):
        date = mdates.date2num(df.index[f.index].to_pydatetime())
        ax1.plot(date, f.price, 'v', color='green', markersize=8, alpha=0.6)

# 当前价格线
current_price = closes[-1]
ax1.axhline(y=current_price, color='purple', linestyle='--', alpha=0.5, label=f'Current: {current_price:.2f}')

ax1.set_title('Shanghai Index (000001.SH) - Chan Theory Analysis\n2 Years Data', fontsize=14)
ax1.set_ylabel('Price', fontsize=12)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper left')

# 笔统计图
ax2 = fig.add_subplot(2, 1, 2)

# 计算每笔的涨跌
bi_returns = []
bi_labels = []
for i, b in enumerate(bis):
    ret = (b.end_price - b.start_price) / b.start_price * 100
    bi_returns.append(ret)
    bi_labels.append(f'Bi{i+1}')

colors_ret = ['red' if r > 0 else 'green' for r in bi_returns]
ax2.bar(range(len(bi_returns)), bi_returns, color=colors_ret, alpha=0.7)

ax2.axhline(y=0, color='black', linewidth=0.5)
ax2.set_title('Bi (笔) Returns - Each Bi Change %', fontsize=14)
ax2.set_ylabel('Return (%)', fontsize=12)
ax2.set_xlabel('Bi Number', fontsize=12)
ax2.grid(True, alpha=0.3)

# 标注最近10笔
if len(bi_returns) > 10:
    for i in range(len(bi_returns)-10, len(bi_returns)):
        ax2.annotate(f'{bi_returns[i]:+.1f}%', (i, bi_returns[i]),
                    ha='center', va='bottom' if bi_returns[i] > 0 else 'top', fontsize=7)

plt.tight_layout()
plt.savefig('D:\\new_tdx_mock\\PYPlugins\\user\\tdx_quant\\chan_chart.png', dpi=150, bbox_inches='tight')
print("\n图片已保存: D:\\new_tdx_mock\\PYPlugins\\user\\tdx_quant\\chan_chart.png")

plt.close('all')

# 打印关键信息
print("\n" + "="*60)
print("  关键点位")
print("="*60)

if bis:
    last_bi = bis[-1]
    print(f"  当前笔: {'上涨' if last_bi.direction == 'up' else '下跌'}")
    print(f"  范围: {last_bi.start_price:.2f} -> {last_bi.end_price:.2f}")

    # 找出最近的高低点
    high_points = [(b.start_price, b.start_idx) for b in bis if b.direction == 'up']
    high_points.extend([(b.end_price, b.end_idx) for b in bis if b.direction == 'up'])
    if high_points:
        hp = max(high_points, key=lambda x: x[0])
        print(f"  近期最高: {hp[0]:.2f} ({str(df.index[min(hp[1], len(df)-1)])[:10]})")

    low_points = [(b.start_price, b.start_idx) for b in bis if b.direction == 'down']
    low_points.extend([(b.end_price, b.end_idx) for b in bis if b.direction == 'down'])
    if low_points:
        lp = min(low_points, key=lambda x: x[0])
        print(f"  近期最低: {lp[0]:.2f} ({str(df.index[min(lp[1], len(df)-1)])[:10]})")

print("="*60)

tq.close()