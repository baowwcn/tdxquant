from tqcenter import tq
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# 初始化
tq.initialize(__file__)

def calculate_indicators(df):
    """计算技术指标"""
    if len(df) < 25:  # 需要足够数据
        return None

    # 确保数据按日期排序
    df = df.sort_values('date')

    # 计算均线
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA10'] = df['close'].rolling(10).mean()
    df['MA20'] = df['close'].rolling(20).mean()

    # 成交量放大倍数 (最近一日成交量 / 前20日均量)
    df['vol_ma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_ma20']

    # 前一日涨幅
    df['prev_change'] = df['close'].pct_change() * 100

    # 5日趋势斜率 (使用线性回归)
    def calc_slope(prices):
        if len(prices) < 5:
            return np.nan
        x = np.arange(5)
        y = prices.values[-5:]
        slope = np.polyfit(x, y, 1)[0]
        return slope / prices.iloc[-1] * 100  # 相对斜率

    df['slope5'] = df['close'].rolling(5).apply(calc_slope, raw=False)

    # 成交量波动系数
    df['vol_std'] = df['volume'].rolling(20).std()
    df['vol_fluctuation'] = df['vol_std'] / df['vol_ma20']

    # 20日波动率
    df['returns'] = df['close'].pct_change()
    df['vol_20d'] = df['returns'].rolling(20).std() * np.sqrt(252) * 100

    return df

def check_conditions(row):
    """检查是否符合涨停前特征"""
    try:
        # 成交量放大 >= 1.3倍
        vol_condition = row['vol_ratio'] >= 1.3

        # 均线排列
        ma5_over_ma10 = row['MA5'] > row['MA10']
        ma10_over_ma20 = row['MA10'] > row['MA20']

        # 动量
        prev_up = row['prev_change'] > 0
        slope_up = row['slope5'] > 0

        # 高概率组合1: 成交量放大 + MA5>MA10 + 前一日上涨
        combo1 = vol_condition and ma5_over_ma10 and prev_up

        # 高概率组合2: 成交量放大>=1.5 + MA10>MA20 + 5日斜率向上
        combo2 = (row['vol_ratio'] >= 1.5) and ma10_over_ma20 and slope_up

        # 强势信号
        strong_vol = row['vol_ratio'] > 2.0
        strong_ma = (row['MA5']/row['MA10'] > 1.05) and (row['MA10']/row['MA20'] > 1.02)
        strong_momentum = (row['prev_change'] > 3) and (row['slope5'] > 5)

        return combo1 or combo2 or (strong_vol and strong_ma and strong_momentum)

    except:
        return False

def main():
    print("开始筛选潜在涨停股票...")

    # 获取所有A股代码
    try:
        all_codes = tq.get_stock_list(market='5')
        print(f"获取到 {len(all_codes)} 只A股股票")
    except Exception as e:
        print(f"获取股票代码失败: {e}")
        return

    # 筛选结果
    potential_stocks = []

    # 为了演示，只处理前100只股票，实际使用时可以去掉限制
    # all_codes = all_codes[:100]

    for i, code in enumerate(all_codes):
        if i % 100 == 0:
            print(f"处理进度: {i}/{len(all_codes)}")

        try:
            # 获取最近60天的日线数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)

            data = tq.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
                stock_list=[code],
                start_time=start_date.strftime('%Y%m%d'),
                end_time=end_date.strftime('%Y%m%d'),
                dividend_type='none',
                period='1d'
            )

            if data is None or len(data) == 0:
                continue

            # 转换为DataFrame
            df = pd.DataFrame(data)
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # 计算指标
            df_with_indicators = calculate_indicators(df)

            if df_with_indicators is None:
                continue

            # 获取最新数据
            latest = df_with_indicators.iloc[-1]

            # 检查是否符合条件
            if check_conditions(latest):
                stock_info = {
                    'code': code,
                    'name': '',  # 可以后续添加
                    'close': latest['close'],
                    'vol_ratio': latest['vol_ratio'],
                    'MA5_over_MA10': latest['MA5'] / latest['MA10'] if latest['MA10'] != 0 else 0,
                    'MA10_over_MA20': latest['MA10'] / latest['MA20'] if latest['MA20'] != 0 else 0,
                    'prev_change': latest['prev_change'],
                    'slope5': latest['slope5'],
                    'vol_fluctuation': latest['vol_fluctuation'],
                    'vol_20d': latest['vol_20d']
                }
                potential_stocks.append(stock_info)

        except Exception as e:
            print(f"处理股票 {code} 时出错: {e}")
            continue

    # 保存结果
    if potential_stocks:
        result_df = pd.DataFrame(potential_stocks)
        result_df.to_csv('potential_ztb_stocks.csv', index=False, encoding='utf-8-sig')
        print(f"找到 {len(potential_stocks)} 只潜在涨停股票，已保存到 potential_ztb_stocks.csv")
        print("前10只股票:")
        print(result_df.head(10))
    else:
        print("未找到符合条件的股票")

if __name__ == "__main__":
    main()