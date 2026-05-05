"""
策略引擎 - 调度器
"""
import time
from typing import List, Optional
from datetime import datetime
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.core.context import Context
from tdx_quant.core.logger import get_logger
from tdx_quant.strategy.base import BaseStrategy

logger = get_logger(__name__)


class Engine:
    """策略引擎"""

    def __init__(self):
        self.strategies: List[BaseStrategy] = []
        self.context = Context()
        self.is_running = False
        self._initialized = False
        self._file_path = __file__

    def add_strategy(self, strategy: BaseStrategy):
        """添加策略"""
        strategy.set_engine(self)
        self.strategies.append(strategy)
        logger.info(f"添加策略: {strategy.name}")

    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
        logger.info(f"移除策略: {strategy_name}")

    def initialize(self, file_path: str = ""):
        """初始化引擎"""
        if self._initialized:
            logger.warning("引擎已初始化")
            return

        path = file_path or self._file_path
        try:
            tq.initialize(path)
            self._initialized = True
            logger.info("TQ数据接口初始化成功")
        except Exception as e:
            logger.error(f"TQ初始化失败: {e}")
            raise

    def stop(self):
        """停止引擎"""
        self.is_running = False
        logger.info("引擎停止")

    def close(self):
        """关闭引擎"""
        self.stop()
        if self._initialized:
            tq.close()
            self._initialized = False
            logger.info("TQ连接已关闭")

    def run_once(self):
        """执行一次（用于回测/分析）"""
        if not self._initialized:
            raise RuntimeError("引擎未初始化，请先调用 initialize()")

        for strategy in self.strategies:
            try:
                strategy.on_bar()
            except Exception as e:
                logger.error(f"策略 {strategy.name} 执行失败: {e}")

    def run_loop(self, interval: int = 60):
        """循环执行（用于实盘）"""
        if not self._initialized:
            raise RuntimeError("引擎未初始化，请先调用 initialize()")

        self.is_running = True
        logger.info(f"开始循环执行，间隔 {interval} 秒")

        while self.is_running:
            try:
                for strategy in self.strategies:
                    strategy.on_bar()
            except Exception as e:
                logger.error(f"执行失败: {e}")

            time.sleep(interval)

    def run(self, mode: str = "once", interval: int = 60):
        """
        运行引擎

        Args:
            mode: "once" 单次执行 / "loop" 循环执行
            interval: 循环间隔（秒）
        """
        if not self._initialized:
            self.initialize()

        if mode == "once":
            self.run_once()
        elif mode == "loop":
            self.run_loop(interval)
        else:
            raise ValueError(f"未知模式: {mode}")

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()