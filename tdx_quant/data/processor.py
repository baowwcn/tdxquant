"""
数据处理
"""
import pandas as pd
import numpy as np
from typing import Optional
from tdx_quant.core.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """数据处理器"""

    @staticmethod
    def resample(df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        周期转换

        Args:
            df: 原始数据（需要包含 open, high, low, close, volume 列）
            period: 目标周期 (5m/15m/30m/1h/1d/1w)

        Returns:
            转换后的数据
        """
        if df.empty:
            return df

        resample_map = {
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "1d": "1D",
            "1w": "1W",
        }

        if period not in resample_map:
            logger.warning(f"不支持的周期: {period}")
            return df

        rule = resample_map[period]

        ohlc = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }

        resampled = df.resample(rule).agg(ohlc).dropna()
        return resampled

    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """计算移动平均线"""
        if periods is None:
            periods = [5, 10, 20, 30, 60, 120, 250]

        result = df.copy()
        for period in periods:
            result[f"ma{period}"] = df["close"].rolling(window=period).mean()

        return result

    @staticmethod
    def calculate_ema(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
        """计算指数移动平均线"""
        if periods is None:
            periods = [5, 10, 20, 30, 60, 120, 250]

        result = df.copy()
        for period in periods:
            result[f"ema{period}"] = df["close"].ewm(span=period, adjust=False).mean()

        return result

    @staticmethod
    def calculate_boll(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """计算布林带"""
        result = df.copy()
        result["boll_mid"] = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        result["boll_up"] = result["boll_mid"] + std_dev * std
        result["boll_down"] = result["boll_mid"] - std_dev * std
        return result

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """计算MACD"""
        result = df.copy()

        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

        result["macd"] = ema_fast - ema_slow
        result["macd_signal"] = result["macd"].ewm(span=signal, adjust=False).mean()
        result["macd_hist"] = result["macd"] - result["macd_signal"]

        return result

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI"""
        result = df.copy()

        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        result["rsi"] = 100 - (100 / (1 + rs))

        return result

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算ATR"""
        result = df.copy()

        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        result["atr"] = true_range.rolling(window=period).mean()

        return result