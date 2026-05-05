"""
策略基类
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from tdx_quant.core.logger import get_logger

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        self.engine = None

    def set_engine(self, engine):
        """设置引擎"""
        self.engine = engine

    @abstractmethod
    def on_bar(self):
        """
        K线回调 - 每个K线/bar触发一次
        子类需要实现此方法
        """
        pass

    def on_init(self):
        """初始化回调 - 策略启动时调用"""
        logger.info(f"策略 {self.name} 初始化")
        pass

    def on_destroy(self):
        """销毁回调 - 策略停止时调用"""
        logger.info(f"策略 {self.name} 销毁")
        pass

    @property
    def context(self):
        """获取上下文"""
        return self.engine.context if self.engine else None