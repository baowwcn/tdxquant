import sys
sys.path.insert(0, r'D:\new_tdx_mock\PYPlugins\user')
from tqcenter import tq
from datetime import datetime, timedelta
from datetime import date

tq.initialize(__file__)

end_time = datetime.now().strftime('%Y%m%d')
start_time = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')

df = tq.get_market_data(
    field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount'],
    stock_list=['000001.SH'],
    start_time=start_time,
    end_time=end_time,
    period='1d',
    fill_data=False
)

if df:
    close_df = tq.price_df(df, 'Close')
    last_7 = close_df.tail(7)

    open_df = tq.price_df(df, 'Open')
    high_df = tq.price_df(df, 'High')
    low_df = tq.price_df(df, 'Low')
    vol_df = tq.price_df(df, 'Volume')

    print('上证指数近7天行情：')
    print('='*70)
    print(f'{"日期":<12} {"开盘":<10} {"最高":<10} {"最低":<10} {"收盘":<10} {"成交量":<12}')
    print('-'*70)

    for idx in last_7.index:
        date_str = idx.strftime('%Y-%m-%d')
        code = '000001.SH'
        open_val = open_df.loc[idx, code]
        high_val = high_df.loc[idx, code]
        low_val = low_df.loc[idx, code]
        close_val = close_df.loc[idx, code]
        vol = int(vol_df.loc[idx, code])
        print(f'{date_str:<12} {open_val:<10.2f} {high_val:<10.2f} {low_val:<10.2f} {close_val:<10.2f} {vol:>12,}')
    print('='*70)
else:
    print('未获取到数据')

tq.close()