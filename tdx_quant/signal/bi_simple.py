"""
宽松版笔识别 - 只保留顶底交替
"""
import pandas as pd
from typing import List
from dataclasses import dataclass
from tdx_quant.signal.fractal import Fractal, detect_fractals


@dataclass
class BiSimple:
    """宽松版笔"""
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    direction: str  # "up" or "down"

    @property
    def length(self) -> float:
        return abs(self.end_price - self.start_price)

    @property
    def high(self) -> float:
        return max(self.start_price, self.end_price)

    @property
    def low(self) -> float:
        return min(self.start_price, self.end_price)

    @property
    def start_date(self) -> str:
        return ""

    @property
    def end_date(self) -> str:
        return ""

    def __repr__(self):
        dir_cn = "↑" if self.direction == "up" else "↓"
        return f"{dir_cn} {self.start_price:.2f} -> {self.end_price:.2f}"


def clean_fractals_simple(fractals: List[Fractal]) -> List[Fractal]:
    """去除连续同类分型（保留极值）"""
    if not fractals:
        return []

    cleaned = [fractals[0]]

    for f in fractals[1:]:
        last = cleaned[-1]

        if f.ftype == last.ftype:
            if f.ftype == "top":
                if f.price > last.price:
                    cleaned[-1] = f
            else:
                if f.price < last.price:
                    cleaned[-1] = f
        else:
            cleaned.append(f)

    return cleaned


def build_simple_bis(fractals: List[Fractal], min_bars: int = 1) -> List[BiSimple]:
    """
    宽松版笔：只要求顶底交替，不要求有效突破
    """
    fractals = clean_fractals_simple(fractals)

    if len(fractals) < 2:
        return []

    bis = []

    for i in range(len(fractals) - 1):
        f1 = fractals[i]
        f2 = fractals[i + 1]

        # 顶底交替
        if f1.ftype == f2.ftype:
            continue

        # 至少隔1根K线
        if f2.index - f1.index < min_bars:
            continue

        direction = "up" if f1.ftype == "bottom" else "down"

        bis.append(BiSimple(
            start_idx=f1.index,
            end_idx=f2.index,
            start_price=f1.price,
            end_price=f2.price,
            direction=direction
        ))

    return bis


def get_simple_chan(df: pd.DataFrame) -> dict:
    """获取宽松版缠论结构"""
    fractals, clean_df = detect_fractals(df)
    bis = build_simple_bis(fractals)

    return {
        "fractals": fractals,
        "bis": bis,
        "fractal_count": len(fractals),
        "bi_count": len(bis),
    }