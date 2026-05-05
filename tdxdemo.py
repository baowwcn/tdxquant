from tqcenter import tq
import pandas as pd

#初始化
tq.initialize(__file__) #所有策略连接通达信客户端都必须调用此函数进行初始化

#获取近3个月上证指数日线数据
data = tq.get_market_data(
        field_list = ['Open', 'High', 'Low', 'Close', 'Volume'],
        stock_list = ["000001.SH"],
        start_time = '20260109',
        end_time = '20260409',
        dividend_type='none',  # 指数数据不需要复权
        period='1d',
    )

# 将字典转换为DataFrame
df = pd.DataFrame({k: v.iloc[:, 0] for k, v in data.items()})
print(df)

# 保存到CSV文件
df.to_csv('shanghai_index_3months.csv', index=True, index_label='Date')
