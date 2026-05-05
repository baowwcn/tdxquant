"""
分型识别 - 标准缠论版（含包含处理）
"""
import pandas as pd
from typing import List, Tuple
from dataclasses import dataclass
from tdx_quant.signal.kline_utils import remove_containment


@dataclass
class Fractal:
    """分型"""
    index: int
    price: float
    ftype: str  # "top" or "bottom"

    def __repr__(self):
        return f"{self.ftype}@{self.index}:{self.price}"


def detect_fractals(df: pd.DataFrame) -> Tuple[List[Fractal], pd.DataFrame]:
    """
    标准缠论分型（含包含处理）

    Args:
        df: K线数据（需要包含 high, low 列）

    Returns:
        (分型列表, 处理后的K线)
    """
    clean_df = remove_containment(df)

    fractals = []

    for i in range(1, len(clean_df) - 1):
        prev = clean_df.iloc[i - 1]
        curr = clean_df.iloc[i]
        next_ = clean_df.iloc[i + 1]

        if curr["high"] > prev["high"] and curr["high"] > next_["high"]:
            fractals.append(Fractal(i, curr["high"], "top"))
        elif curr["low"] < prev["low"] and curr["low"] < next_["low"]:
            fractals.append(Fractal(i, curr["low"], "bottom"))

    return fractals, clean_df


def detect_fractals_simple(kline: pd.DataFrame) -> List[Fractal]:
    """
    简化版分型识别（不含包含处理）

    Args:
        kline: K线数据

    Returns:
        分型列表
    """
    if len(kline) < 3:
        return []

    fractals = []

    for i in range(1, len(kline) - 1):
        prev = kline.iloc[i - 1]
        curr = kline.iloc[i]
        next_ = kline.iloc[i + 1]

        if curr["high"] > prev["high"] and curr["high"] > next_["high"]:
            fractals.append(Fractal(i, curr["high"], "top"))
        elif curr["low"] < prev["low"] and curr["low"] < next_["low"]:
            fractals.append(Fractal(i, curr["low"], "bottom"))

    return fractals


def get_fractal_info(df: pd.DataFrame) -> dict:
    """获取分型详细信息"""
    fractals, clean_df = detect_fractals(df)

    return {
        "fractals": fractals,
        "clean_df": clean_df,
        "original_len": len(df),
        "clean_len": len(clean_df),
        "merged_count": len(df) - len(clean_df)
    }