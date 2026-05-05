import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.data.fetcher import DataFetcher

tq.initialize(__file__)
fetcher = DataFetcher()
df = fetcher.get_kline(code="000001.SH", period="1d", count=500)

print(f"K线数量: {len(df)}")
print(f"起始: {str(df.index[0])[:10]}")
print(f"结束: {str(df.index[-1])[:10]}")

tq.close()