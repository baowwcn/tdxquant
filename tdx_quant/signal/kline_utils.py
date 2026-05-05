"""
K线工具 - 包含关系处理
"""
import pandas as pd
import numpy as np
from typing import Tuple


def is_contain(k1, k2) -> bool:
    """判断是否存在包含关系"""
    return (k1["high"] >= k2["high"] and k1["low"] <= k2["low"]) or \
           (k2["high"] >= k1["high"] and k2["low"] <= k1["low"])


def merge_kline(k1, k2, direction: str) -> dict:
    """
    合并K线

    Args:
        k1, k2: K线数据
        direction: "up" 上涨 / "down" 下跌

    Returns:
        合并后的K线
    """
    if direction == "up":
        high = max(k1["high"], k2["high"])
        low = max(k1["low"], k2["low"])
    else:
        high = min(k1["high"], k2["high"])
        low = min(k1["low"], k2["low"])

    return {"high": high, "low": low}


def remove_containment(df: pd.DataFrame) -> pd.DataFrame:
    """
    去除K线包含关系

    Args:
        df: 原始K线数据（需要包含 high, low 列）

    Returns:
        去除包含关系后的K线
    """
    if len(df) < 2:
        return df.copy()

    result = []

    for i in range(len(df)):
        curr = df.iloc[i]

        if not result:
            result.append(curr.copy())
            continue

        last = result[-1]

        if is_contain(last, curr):
            if len(result) >= 2:
                prev = result[-2]
                direction = "up" if last["high"] > prev["high"] else "down"
            else:
                direction = "up"

            merged = merge_kline(last, curr, direction)
            result[-1] = pd.Series(merged)
        else:
            result.append(curr.copy())

    return pd.DataFrame(result).reset_index(drop=True)


def get_clean_kline(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    获取清洁K线（处理包含关系）

    Returns:
        (原始K线, 处理后的K线)
    """
    clean_df = remove_containment(df)
    return df, clean_df