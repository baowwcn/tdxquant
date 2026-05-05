"""
持仓管理
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from tdx_quant.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Position:
    """持仓"""
    code: str
    volume: int
    avg_cost: float
    current_price: float = 0
    market_value: float = 0
    profit: float = 0
    profit_pct: float = 0


class PositionManager:
    """持仓管理器"""

    def __init__(self, initial_cash: float = 1000000):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}

    def update_position(
        self,
        code: str,
        volume: int,
        price: float,
        avg_cost: float = 0
    ):
        """更新持仓"""
        if code in self.positions:
            pos = self.positions[code]
            pos.volume = volume
            pos.current_price = price
            pos.market_value = volume * price
            if pos.volume > 0:
                pos.profit = (price - pos.avg_cost) * volume
                pos.profit_pct = (price - pos.avg_cost) / pos.avg_cost * 100
        else:
            self.positions[code] = Position(
                code=code,
                volume=volume,
                avg_cost=avg_cost,
                current_price=price,
                market_value=volume * price
            )

    def get_position(self, code: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(code)

    def get_total_value(self) -> float:
        """获取总资产"""
        total = self.cash
        for pos in self.positions.values():
            total += pos.market_value
        return total

    def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())

    def __repr__(self):
        return f"PositionManager(cash={self.cash}, positions={len(self.positions)})"