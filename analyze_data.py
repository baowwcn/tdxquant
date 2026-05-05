import pandas as pd
import numpy as np

# 读取CSV文件
df = pd.read_csv('shanghai_index_3months.csv', index_col='Date', parse_dates=True)

# 基本信息
print('=== 上证指数近3个月数据分析 ===')
print(f'数据时间范围: {df.index.min()} 到 {df.index.max()}')
print(f'总交易日数: {len(df)}')

# 价格统计
print('\n=== 价格统计 ===')
print(f'起始收盘价: {df["Close"].iloc[0]:.2f}')
print(f'结束收盘价: {df["Close"].iloc[-1]:.2f}')
print(f'最高价: {df["High"].max():.2f} (日期: {df["High"].idxmax()})')
print(f'最低价: {df["Low"].min():.2f} (日期: {df["Low"].idxmin()})')
print(f'平均收盘价: {df["Close"].mean():.2f}')
print(f'收盘价标准差: {df["Close"].std():.2f}')

# 涨跌幅
total_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
print(f'\n总涨跌幅: {total_return:.2f}%')

# 月度分析
df['Month'] = df.index.month
monthly_stats = df.groupby('Month')['Close'].agg(['first', 'last', 'max', 'min'])
monthly_stats['Return'] = (monthly_stats['last'] - monthly_stats['first']) / monthly_stats['first'] * 100
print('\n=== 月度表现 ===')
for month, row in monthly_stats.iterrows():
    month_name = ['Jan', 'Feb', 'Mar', 'Apr'][month-1]
    print(f'{month_name}: 起始 {row["first"]:.2f}, 结束 {row["last"]:.2f}, 最高 {row["max"]:.2f}, 最低 {row["min"]:.2f}, 涨跌幅 {row["Return"]:.2f}%')

# 成交量分析
print('\n=== 成交量分析 ===')
print(f'平均日成交量: {df["Volume"].mean():.0f}')
print(f'最高日成交量: {df["Volume"].max():.0f} (日期: {df["Volume"].idxmax()})')
print(f'最低日成交量: {df["Volume"].min():.0f} (日期: {df["Volume"].idxmin()})')

# 波动性分析
daily_returns = df['Close'].pct_change()
volatility = daily_returns.std() * np.sqrt(252) * 100  # 年化波动率
print(f'\n年化波动率: {volatility:.2f}%')

# 趋势分析
print('\n=== 趋势分析 ===')
if total_return > 0:
    print('整体呈上涨趋势')
else:
    print('整体呈下跌趋势')

# 近期表现
recent_10 = df.tail(10)
recent_return = (recent_10['Close'].iloc[-1] - recent_10['Close'].iloc[0]) / recent_10['Close'].iloc[0] * 100
print(f'最近10个交易日涨跌幅: {recent_return:.2f}%')