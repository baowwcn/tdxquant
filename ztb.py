from tqcenter import tq
import pandas as pd
import os
from datetime import datetime, timedelta

# 初始化
tq.initialize(__file__)

# 创建ztb目录
os.makedirs('ztb', exist_ok=True)

# 获取A股股票列表 (market='5' 表示A股)
print("获取A股股票列表...")
stock_list = tq.get_stock_list(market='5')
print(f"共获取到 {len(stock_list)} 只A股股票")

# 筛选今日涨停板股票
limit_up_stocks = []
print("筛选今日涨停板股票...")

for stock_code in stock_list:
    try:
        snapshot = tq.get_market_snapshot(stock_code, field_list=['Now', 'LastClose'])
        if snapshot and 'Now' in snapshot and 'LastClose' in snapshot:
            now = float(snapshot['Now'])
            last_close = float(snapshot['LastClose'])
            if last_close > 0:
                pct_change = (now - last_close) / last_close
                if pct_change >= 0.099:  # 涨幅 >= 9.9% 视为涨停
                    limit_up_stocks.append((stock_code, pct_change))
    except Exception:
        continue

limit_up_stocks.sort(key=lambda x: x[1], reverse=True)
print(f"今日涨停板股票数量: {len(limit_up_stocks)}")
for code, pct in limit_up_stocks[:20]:
    print(f"{code}: 涨幅 {pct:.2%}")

limit_up_stocks = [code for code, pct in limit_up_stocks]

# 计算近3个月的时间范围
today = datetime.now()
three_months_ago = today - timedelta(days=90)
start_date = three_months_ago.strftime('%Y%m%d')
end_date = today.strftime('%Y%m%d')

print(f"数据时间范围: {start_date} 到 {end_date}")

# 为每个涨停股获取近3个月数据并保存
for stock_code in limit_up_stocks:
    try:
        print(f"获取 {stock_code} 的历史数据...")
        data = tq.get_market_data(
            field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
            stock_list=[stock_code],
            start_time=start_date,
            end_time=end_date,
            dividend_type='none',
            period='1d'
        )

        # 转换为DataFrame
        df = pd.DataFrame({k: v.iloc[:, 0] for k, v in data.items()})

        # 保存到CSV文件
        filename = f"ztb/{stock_code.replace('.', '_')}.csv"
        df.to_csv(filename, index=True, index_label='Date')
        print(f"已保存 {stock_code} 数据到 {filename}")

    except Exception as e:
        print(f"处理 {stock_code} 失败: {e}")
        continue

print("所有涨停板股票数据获取完成！")
