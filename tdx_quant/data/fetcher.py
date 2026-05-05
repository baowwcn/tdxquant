"""
数据获取
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
from tdx_quant.core.logger import get_logger
from tdx_quant.config import DATA_CONFIG

logger = get_logger(__name__)


class DataFetcher:
    """行情数据获取器"""

    def __init__(self):
        self.default_period = DATA_CONFIG["default_period"]
        self.default_dividend = DATA_CONFIG["default_dividend_type"]

    def get_kline(
        self,
        code: str,
        period: str = "",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = ""
    ) -> Optional[pd.DataFrame]:
        """
        获取K线数据

        Args:
            code: 股票代码 (如 000001.SH)
            period: 周期 (1m/5m/15m/30m/1h/1d/1w/1mon)
            start_time: 开始时间 YYYYMMDD
            end_time: 结束时间 YYYYMMDD
            count: 数据条数（-1表示使用时间范围）
            dividend_type: 复权类型 (none/front/back)

        Returns:
            DataFrame 或 None
        """
        period = period or self.default_period
        dividend_type = dividend_type or self.default_dividend

        try:
            df = tq.get_market_data(
                field_list=["Date", "Time", "Open", "High", "Low", "Close", "Volume", "Amount"],
                stock_list=[code],
                start_time=start_time,
                end_time=end_time,
                count=count,
                period=period,
                dividend_type=dividend_type,
                fill_data=True
            )

            if not df or "Close" not in df:
                logger.warning(f"未获取到 {code} 的数据")
                return None

            close_df = tq.price_df(df, "Close")
            open_df = tq.price_df(df, "Open")
            high_df = tq.price_df(df, "High")
            low_df = tq.price_df(df, "Low")
            vol_df = tq.price_df(df, "Volume")

            result = pd.DataFrame({
                "datetime": close_df.index,
                "open": open_df[code].values,
                "high": high_df[code].values,
                "low": low_df[code].values,
                "close": close_df[code].values,
                "volume": vol_df[code].values
            })
            result.set_index("datetime", inplace=True)

            return result

        except Exception as e:
            logger.error(f"获取 {code} K线失败: {e}")
            return None

    def get_realtime_quote(self, code: str) -> Optional[Dict]:
        """获取实时行情快照"""
        try:
            data = tq.get_market_snapshot(stock_code=code)
            if data and data.get("ErrorId") == "0":
                return data
            return None
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None

    def get_stock_info(self, code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            info = tq.get_stock_info(stock_code=code)
            return info if info else None
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None