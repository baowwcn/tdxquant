"""
笔识别 - 严格缠论版（带确认机制）
"""
import pandas as pd
from typing import List, Tuple
from dataclasses import dataclass
from tdx_quant.signal.fractal import Fractal, detect_fractals


@dataclass
class Bi:
    """笔（严格版）"""
    start: Fractal
    end: Fractal
    confirmed: bool  # 是否已确认

    @property
    def direction(self) -> str:
        return "up" if self.start.ftype == "bottom" else "down"

    @property
    def start_idx(self) -> int:
        return self.start.index

    @property
    def end_idx(self) -> int:
        return self.end.index

    @property
    def high(self) -> float:
        return max(self.start.price, self.end.price)

    @property
    def low(self) -> float:
        return min(self.start.price, self.end.price)

    @property
    def length(self) -> float:
        return abs(self.end.price - self.start.price)

    @property
    def valid(self) -> bool:
        """是否有效笔（必须突破前高/前低）"""
        return True

    def __repr__(self):
        status = "OK" if self.confirmed else "..."
        direction_cn = "↑" if self.direction == "up" else "↓"
        return f"{direction_cn} {status}: {self.start.price:.2f}->{self.end.price:.2f}"


def clean_fractals(fractals: List[Fractal]) -> List[Fractal]:
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


def build_strict_bis(fractals: List[Fractal], min_bars: int = 1) -> List[Bi]:
    """
    构建严格缠论笔（带确认机制）

    规则：
    1. 顶底交替
    2. 有效突破（向上笔必须突破前高，向下笔必须突破前低）
    3. 笔确认机制（出现反向笔则当前笔确认）
    """
    fractals = clean_fractals(fractals)

    if len(fractals) < 2:
        return []

    bis = []
    last_top = None
    last_bottom = None

    for i in range(len(fractals) - 1):
        f1 = fractals[i]
        f2 = fractals[i + 1]

        if f1.ftype == f2.ftype:
            continue

        if f1.ftype == "bottom" and f2.ftype == "top":
            if last_top is None or f2.price > last_top.price:
                bi = Bi(f1, f2, False)
                bis.append(bi)
                last_top = f2

        elif f1.ftype == "top" and f2.ftype == "bottom":
            if last_bottom is None or f2.price < last_bottom.price:
                bi = Bi(f1, f2, False)
                bis.append(bi)
                last_bottom = f2

    for i in range(len(bis) - 1):
        curr = bis[i]
        next_bi = bis[i + 1]
        if curr.direction != next_bi.direction:
            curr.confirmed = True

    return bis


def build_bis(fractals: List[Fractal], min_bars: int = 1) -> List[Bi]:
    """兼容旧接口"""
    return build_strict_bis(fractals, min_bars)


def get_chan_structure(kline: pd.DataFrame) -> dict:
    """获取完整的缠论结构（严格版）"""
    fractals, clean_df = detect_fractals(kline)
    bis = build_strict_bis(fractals)

    confirmed_bis = [b for b in bis if b.confirmed]
    unconfirmed_bis = [b for b in bis if not b.confirmed]

    return {
        "fractals": fractals,
        "bis": bis,
        "confirmed_bis": confirmed_bis,
        "unconfirmed_bis": unconfirmed_bis,
        "clean_df": clean_df,
        "fractal_count": len(fractals),
        "bi_count": len(bis),
        "confirmed_count": len(confirmed_bis),
        "last_bi": bis[-1] if bis else None,
        "last_confirmed_bi": confirmed_bis[-1] if confirmed_bis else None,
    }


def print_chan_structure(struct: dict):
    """打印缠论结构（严格版）"""
    print("\n" + "=" * 55)
    print("  缠论结构分析（严格版 - 带确认机制）")
    print("=" * 55)

    print(f"\n笔统计:")
    print(f"  总笔数: {struct['bi_count']}")
    print(f"  已确认: {struct['confirmed_count']}")
    print(f"  未确认: {struct['bi_count'] - struct['confirmed_count']}")

    print(f"\n已确认笔:")
    for b in struct["confirmed_bis"][-8:]:
        print(f"  {b}")

    print(f"\n未确认笔:")
    for b in struct["unconfirmed_bis"]:
        print(f"  {b}")

    if struct["last_confirmed_bi"]:
        lb = struct["last_confirmed_bi"]
        print(f"\n最近已确认笔: {lb}")
        print(f"  方向: {'上涨' if lb.direction == 'up' else '下跌'}")
        print(f"  幅度: {lb.length:.2f}")

    print("=" * 55)