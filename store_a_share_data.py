import sqlite3
import pandas as pd
from tqcenter import tq
import os
from datetime import datetime, timedelta

# 初始化
tq.initialize(__file__)

# 创建数据库
db_path = 'a_share_monthly.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS stock_data (
    code TEXT,
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    PRIMARY KEY (code, date)
)
''')
conn.commit()

# 获取A股股票列表
print("获取A股股票列表...")
stock_list = tq.get_stock_list(market='5')
print(f"共获取到 {len(stock_list)} 只A股股票")

# 计算近一个月的时间范围
today = datetime.now()
one_month_ago = today - timedelta(days=30)
start_date = one_month_ago.strftime('%Y%m%d')
end_date = today.strftime('%Y%m%d')

print(f"数据时间范围: {start_date} 到 {end_date}")

# 批量获取和存储数据
batch_size = 100  # 每批处理100只股票
total_stocks = len(stock_list)

for i in range(0, total_stocks, batch_size):
    batch_stocks = stock_list[i:i+batch_size]
    print(f"处理第 {i+1} 到 {min(i+batch_size, total_stocks)} 只股票...")

    for stock_code in batch_stocks:
        try:
            # 获取近一个月数据
            data = tq.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume'],
                stock_list=[stock_code],
                start_time=start_date,
                end_time=end_date,
                dividend_type='none',
                period='1d'
            )

            if data and 'Close' in data:
                # 转换为DataFrame
                df = pd.DataFrame({k: v.iloc[:, 0] for k, v in data.items()})

                # 准备数据插入
                records = []
                for idx, row in df.iterrows():
                    records.append((
                        stock_code,
                        idx.strftime('%Y-%m-%d'),
                        row['Open'],
                        row['High'],
                        row['Low'],
                        row['Close'],
                        row['Volume']
                    ))

                # 批量插入
                cursor.executemany('''
                INSERT OR REPLACE INTO stock_data (code, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', records)

                print(f"已存储 {stock_code} 数据，{len(records)} 条记录")

        except Exception as e:
            print(f"处理 {stock_code} 失败: {e}")
            continue

    # 每批提交一次
    conn.commit()
    print(f"第 {i//batch_size + 1} 批完成，已提交到数据库")

print("所有A股股票近一个月数据存储完成！")
conn.close()