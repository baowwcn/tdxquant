import os
import pandas as pd
import numpy as np

ZTBDIR = 'ztb'
short = 5
medium = 10
long = 20

records = []
for fname in sorted(os.listdir(ZTBDIR)):
    if not fname.endswith('.csv'):
        continue
    code = fname.replace('.csv', '').replace('_', '.')
    path = os.path.join(ZTBDIR, fname)
    try:
        df = pd.read_csv(path, parse_dates=['Date'], index_col='Date')
    except Exception as e:
        print('跳过无效文件', fname, '原因:', e)
        continue
    if len(df) < long + 2:
        continue
    # assume last row is limit-up day
    limit_day = df.index.max()
    prev_day = df.index[-2]
    # compute moving averages on prev day
    df['MA5'] = df['Close'].rolling(short).mean()
    df['MA10'] = df['Close'].rolling(medium).mean()
    df['MA20'] = df['Close'].rolling(long).mean()
    if pd.isna(df.loc[prev_day, 'MA5']) or pd.isna(df.loc[prev_day, 'MA10']) or pd.isna(df.loc[prev_day, 'MA20']):
        continue
    vol_before = df.loc[prev_day, 'Volume']
    avg_vol_5 = df['Volume'].iloc[-7:-2].mean() if len(df) >= 7 else np.nan
    avg_vol_20 = df['Volume'].iloc[-22:-2].mean() if len(df) >= 22 else np.nan
    vol_ratio_5_20 = vol_before / avg_vol_20 if avg_vol_20 > 0 else np.nan
    ma5 = df.loc[prev_day, 'MA5']
    ma10 = df.loc[prev_day, 'MA10']
    ma20 = df.loc[prev_day, 'MA20']
    close_before = df.loc[prev_day, 'Close']
    close_before_2 = df['Close'].iloc[-3]
    slope5 = (close_before - df['Close'].iloc[-6]) / df['Close'].iloc[-6] if len(df) >= 6 else np.nan
    # 计算更多指标
    returns = df['Close'].pct_change().dropna()
    vol_20d = returns.iloc[-22:-2].std() * np.sqrt(252) if len(returns) >= 22 else np.nan  # 20日波动率
    vol_ratio = df['Volume'].iloc[-7:-2].std() / df['Volume'].iloc[-22:-2].mean() if len(df) >= 22 else np.nan  # 成交量波动系数
    
    records.append({
        'code': code,
        'limit_day': limit_day.strftime('%Y-%m-%d'),
        'prev_day': prev_day.strftime('%Y-%m-%d'),
        'close_prev': close_before,
        'vol_prev': vol_before,
        'avg_vol_5_pre': avg_vol_5,
        'avg_vol_20_pre': avg_vol_20,
        'vol_ratio_5_20': vol_ratio_5_20,
        'vol_20d': vol_20d,
        'vol_fluctuation': vol_ratio,
        'MA5': ma5,
        'MA10': ma10,
        'MA20': ma20,
        'MA5_over_MA10': ma5 / ma10 if ma10 != 0 else np.nan,
        'MA10_over_MA20': ma10 / ma20 if ma20 != 0 else np.nan,
        'prev_close_change': (close_before - close_before_2) / close_before_2 if close_before_2 > 0 else np.nan,
        'slope5': slope5,
    })

summary = pd.DataFrame(records)
print('records length:', len(records))
if 'vol_ratio_5_20' in summary.columns:
    summary = summary.sort_values('vol_ratio_5_20', ascending=False)
else:
    print('no vol_ratio_5_20 column, columns=', summary.columns.tolist())
summary.to_csv('ztb/ztb_analysis_summary.csv', index=False)
print('分析完成，共', len(summary), '只股票')
if 'vol_ratio_5_20' in summary.columns:
    print(summary[['code','prev_day','vol_prev','avg_vol_20_pre','vol_ratio_5_20','vol_20d','vol_fluctuation','MA5','MA10','MA20','MA5_over_MA10','MA10_over_MA20','prev_close_change','slope5']].head(20).to_string(index=False))

# aggregate statistics
print('\n总体统计:')
print('平均涨停前日成交量/20日均量:', summary['vol_ratio_5_20'].mean())
print('平均20日波动率:', summary['vol_20d'].mean())
print('平均成交量波动系数:', summary['vol_fluctuation'].mean())
print('MA5/MA10 平均值:', summary['MA5_over_MA10'].mean())
print('MA10/MA20 平均值:', summary['MA10_over_MA20'].mean())
print('MA5 > MA10 比例:', (summary['MA5_over_MA10'] > 1).mean())
print('MA10 > MA20 比例:', (summary['MA10_over_MA20'] > 1).mean())
print('前一日涨幅 > 0 比例:', (summary['prev_close_change'] > 0).mean())
print('5日斜率 > 0 比例:', (summary['slope5'] > 0).mean())

print('\n成交量超过20日均量比例:', (summary['vol_ratio_5_20'] > 1).mean())
print('成交量超过30%比例:', (summary['vol_ratio_5_20'] > 1.3).mean())
print('成交量超过50%比例:', (summary['vol_ratio_5_20'] > 1.5).mean())
print('波动率 > 30% 比例:', (summary['vol_20d'] > 0.3).mean())
