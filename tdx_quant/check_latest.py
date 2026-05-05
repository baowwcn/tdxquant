import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.signal.fractal import detect_fractals
from tdx_quant.signal.bi import build_strict_bis
from datetime import datetime, timedelta

tq.initialize(__file__)
fetcher = DataFetcher()

# 获取最近60天数据
df = fetcher.get_kline(code="000001.SH", period="1d", count=60)

print("=" * 60)
print("  上证指数近期分析")
print("=" * 60)

print(f"\n数据范围: {str(df.index[0])[:10]} - {str(df.index[-1])[:10]}")
print(f"共 {len(df)} 个交易日")

# 最近5天行情
print("\n【最近5日行情】")
for i in range(-5, 0):
    date = df.index[i]
    row = df.iloc[i]
    change = (row["close"] - df.iloc[i-1]["close"]) / df.iloc[i-1]["close"] * 100
    sign = "+" if change >= 0 else ""
    print(f"  {str(date)[:10]} 收盘:{row['close']:.2f} 涨跌:{sign}{change:.2f}%")

# 缠论分析
fractals, clean_df = detect_fractals(df)
bis = build_strict_bis(fractals)

confirmed = [b for b in bis if b.confirmed]
unconfirmed = [b for b in bis if not b.confirmed]

print("\n【缠论笔结构】")
print(f"  已确认笔: {len(confirmed)}个")
print(f"  未确认笔: {len(unconfirmed)}个")

if unconfirmed:
    print("\n  最近3个未确认笔:")
    for b in unconfirmed[-3:]:
        direction = "上涨" if b.direction == "up" else "下跌"
        print(f"    {direction}: {b.start.price:.2f} -> {b.end.price:.2f}")

# 当前价格位置
current = df.iloc[-1]
print("\n【当前价格位置】")
print(f"  收盘: {current['close']:.2f}")
print(f"  60日最高: {df['high'].max():.2f}")
print(f"  60日最低: {df['low'].min():.2f}")
print(f"  当前在60日区间位置: {(current['close'] - df['low'].min()) / (df['high'].max() - df['low'].min()) * 100:.1f}%")

# 技术指标
delta = df["close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs)).iloc[-1]

print(f"\n【技术指标】")
print(f"  RSI(14): {rsi:.1f}")

# 均线
ma5 = df["close"].rolling(5).mean().iloc[-1]
ma10 = df["close"].rolling(10).mean().iloc[-1]
ma20 = df["close"].rolling(20).mean().iloc[-1]
print(f"  MA5: {ma5:.2f}")
print(f"  MA10: {ma10:.2f}")
print(f"  MA20: {ma20:.2f}")

print("\n" + "=" * 60)
print("  分析结论")
print("=" * 60)

# 判断
if rsi > 70:
    status = "超买区域，风险较大"
elif rsi < 30:
    status = "超卖区域，可能反弹"
else:
    status = "中性区域"

if current['close'] > ma20:
    trend = "短期偏多"
else:
    trend = "短期偏空"

print(f"  整体状态: {status}")
print(f"  均线趋势: {trend}")
print(f"  建议: 谨慎操作，等待方向明确")

tq.close()