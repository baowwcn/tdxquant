"""
交易执行
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq, tqconst
from typing import Optional, Dict
from tdx_quant.core.logger import get_logger
from tdx_quant.config import TRADE_CONFIG

logger = get_logger(__name__)


class Trader:
    """交易执行器"""

    def __init__(self, account_id: int = -1):
        self.account_id = account_id

    def set_account(self, account_id: int):
        """设置账户"""
        self.account_id = account_id

    def buy(
        self,
        code: str,
        price: float = 0,
        volume: int = 100,
        price_type: int = 0
    ) -> Dict:
        """
        买入

        Args:
            code: 股票代码
            price: 价格（0表示市价）
            volume: 数量
            price_type: 价格类型 (0:限价, 1:市价)

        Returns:
            委托结果
        """
        if self.account_id < 0:
            logger.error("未设置账户")
            return {"ErrorId": "-1", "Error": "未设置账户"}

        logger.info(f"买入: {code} 价格={price} 数量={volume}")

        try:
            result = tq.order_stock(
                account_id=self.account_id,
                stock_code=code,
                order_type=tqconst.STOCK_BUY,
                order_volume=volume,
                price_type=price_type,
                price=price
            )
            return result
        except Exception as e:
            logger.error(f"买入失败: {e}")
            return {"ErrorId": "-1", "Error": str(e)}

    def sell(
        self,
        code: str,
        price: float = 0,
        volume: int = 100,
        price_type: int = 0
    ) -> Dict:
        """
        卖出

        Args:
            code: 股票代码
            price: 价格（0表示市价）
            volume: 数量
            price_type: 价格类型

        Returns:
            委托结果
        """
        if self.account_id < 0:
            logger.error("未设置账户")
            return {"ErrorId": "-1", "Error": "未设置账户"}

        logger.info(f"卖出: {code} 价格={price} 数量={volume}")

        try:
            result = tq.order_stock(
                account_id=self.account_id,
                stock_code=code,
                order_type=tqconst.STOCK_SELL,
                order_volume=volume,
                price_type=price_type,
                price=price
            )
            return result
        except Exception as e:
            logger.error(f"卖出失败: {e}")
            return {"ErrorId": "-1", "Error": str(e)}

    def cancel_order(self, order_id: str, code: str = "") -> Dict:
        """撤单"""
        if self.account_id < 0:
            return {"ErrorId": "-1", "Error": "未设置账户"}

        try:
            result = tq.cancel_order_stock(
                account_id=self.account_id,
                stock_code=code,
                order_id=order_id
            )
            return result
        except Exception as e:
            logger.error(f"撤单失败: {e}")
            return {"ErrorId": "-1", "Error": str(e)}