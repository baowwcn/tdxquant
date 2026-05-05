"""
上下文 - 用于共享数据（类似 backtrader）
"""
from typing import Dict, Any, Optional
from datetime import datetime


class Context:
    """策略运行上下文"""

    def __init__(self):
        self.current_bar: Optional[Dict[str, Any]] = None
        self.current_time: Optional[datetime] = None
        self.position: Dict[str, float] = {}  # 持仓 {code: volume}
        self.cash: float = 0  # 可用资金
        self.total_value: float = 0  # 总资产
        self.strategy_data: Dict[str, Any] = {}  # 策略私有数据

    def update_bar(self, code: str, bar: Dict[str, Any]):
        """更新当前K线"""
        self.current_bar = bar
        self.current_time = bar.get("datetime")
        self.current_code = code

    def update_position(self, code: str, volume: float):
        """更新持仓"""
        self.position[code] = volume

    def update_cash(self, cash: float):
        """更新可用资金"""
        self.cash = cash

    def get_position(self, code: str) -> float:
        """获取持仓"""
        return self.position.get(code, 0)

    def set_strategy_data(self, key: str, value: Any):
        """设置策略数据"""
        self.strategy_data[key] = value

    def get_strategy_data(self, key: str, default=None) -> Any:
        """获取策略数据"""
        return self.strategy_data.get(key, default)

    def __repr__(self):
        return f"Context(cash={self.cash}, position={self.position}, time={self.current_time})"