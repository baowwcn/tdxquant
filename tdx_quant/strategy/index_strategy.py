"""
上证指数分析策略
"""
import pandas as pd
from typing import Optional, Dict, Any
from tdx_quant.strategy.base import BaseStrategy
from tdx_quant.data.fetcher import DataFetcher
from tdx_quant.data.processor import DataProcessor
from tdx_quant.config import MARKET_CONFIG, STRATEGY_CONFIG
from tdx_quant.core.logger import get_logger
from tdx_quant.signal.strategy_signal import generate_signal

logger = get_logger(__name__)


class IndexStrategy(BaseStrategy):
    """指数分析策略"""

    def __init__(self, index_code: str = "000001.SH"):
        super().__init__(STRATEGY_CONFIG.get("name", "IndexStrategy"))
        self.index_code = index_code
        self.data_fetcher = DataFetcher()
        self.processor = DataProcessor()
        self.history_data: Optional[pd.DataFrame] = None

    def on_init(self):
        """初始化策略"""
        super().on_init()
        logger.info(f"初始化策略: {self.index_code}")

    def load_data(self, count: int = 500, period: str = "1d") -> bool:
        """加载历史数据"""
        logger.info(f"加载 {self.index_code} 数据...")

        self.history_data = self.data_fetcher.get_kline(
            code=self.index_code,
            period=period,
            count=count
        )

        if self.history_data is None or self.history_data.empty:
            logger.error(f"数据加载失败: {self.index_code}")
            return False

        logger.info(f"数据加载成功，共 {len(self.history_data)} 条")
        return True

    def analyze(self) -> Dict[str, Any]:
        """
        执行分析

        Returns:
            分析结果字典
        """
        if self.history_data is None or self.history_data.empty:
            return {"error": "无数据"}

        df = self.history_data.copy()

        df = self.processor.calculate_ma(df)
        df = self.processor.calculate_boll(df)
        df = self.processor.calculate_macd(df)
        df = self.processor.calculate_rsi(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else None

        result = {
            "code": self.index_code,
            "date": str(df.index[-1])[:10],
            "close": float(latest["close"]),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "volume": float(latest["volume"]),
            "ma5": float(latest.get("ma5", 0)),
            "ma10": float(latest.get("ma10", 0)),
            "ma20": float(latest.get("ma20", 0)),
            "ma60": float(latest.get("ma60", 0)),
            "boll_mid": float(latest.get("boll_mid", 0)),
            "boll_up": float(latest.get("boll_up", 0)),
            "boll_down": float(latest.get("boll_down", 0)),
            "macd": float(latest.get("macd", 0)),
            "macd_signal": float(latest.get("macd_signal", 0)),
            "macd_hist": float(latest.get("macd_hist", 0)),
            "rsi": float(latest.get("rsi", 0)),
        }

        if prev is not None:
            result["prev_close"] = float(prev["close"])
            result["change_pct"] = (result["close"] - result["prev_close"]) / result["prev_close"] * 100

        return result

    def print_analysis(self):
        """打印分析结果"""
        result = self.analyze()

        if "error" in result:
            print(f"分析失败: {result['error']}")
            return

        print("\n" + "=" * 60)
        print(f"  {self.index_code} 技术分析")
        print("=" * 60)
        print(f"  日期: {result.get('date', 'N/A')}")
        print(f"  收盘: {result.get('close', 0):.2f}")
        print(f"  涨跌: {result.get('change_pct', 0):+.2f}%")
        print("-" * 60)
        print(f"  均线: MA5={result.get('ma5', 0):.2f} MA10={result.get('ma10', 0):.2f}")
        print(f"       MA20={result.get('ma20', 0):.2f} MA60={result.get('ma60', 0):.2f}")
        print("-" * 60)
        print(f"  布林: 中轨={result.get('boll_mid', 0):.2f}")
        print(f"       上轨={result.get('boll_up', 0):.2f} 下轨={result.get('boll_down', 0):.2f}")
        print("-" * 60)
        print(f"  MACD: {result.get('macd', 0):.4f} 信号={result.get('macd_signal', 0):.4f}")
        print(f"       柱体={result.get('macd_hist', 0):.4f}")
        print("-" * 60)
        print(f"  RSI: {result.get('rsi', 0):.2f}")
        print("=" * 60)

    def on_bar(self):
        """K线回调 - 每次执行分析"""
        if self.history_data is None:
            self.load_data()

        if self.history_data is not None:
            self.print_analysis()

    def run(self):
        """运行策略（单次）"""
        self.on_init()
        self.load_data()
        self.on_bar()
        self.on_destroy()
        return self.analyze()