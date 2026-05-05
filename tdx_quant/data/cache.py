"""
本地缓存
"""
import os
import pickle
from pathlib import Path
from typing import Optional, Any
import pandas as pd
from datetime import datetime, timedelta
from tdx_quant.core.logger import get_logger
from tdx_quant.config import DATA_CONFIG

logger = get_logger(__name__)


class DataCache:
    """本地数据缓存"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.enabled = DATA_CONFIG["cache_enabled"]

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.pkl"

    def get(self, key: str, max_age_minutes: int = 30) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键
            max_age_minutes: 最大缓存时间（分钟）

        Returns:
            缓存数据或 None
        """
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
            age = datetime.now() - mtime

            if age > timedelta(minutes=max_age_minutes):
                logger.debug(f"缓存已过期: {key}")
                return None

            with open(cache_path, "rb") as f:
                data = pickle.load(f)
                logger.debug(f"读取缓存: {key}")
                return data

        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None

    def set(self, key: str, data: Any):
        """设置缓存"""
        if not self.enabled:
            return

        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)
                logger.debug(f"写入缓存: {key}")
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")

    def delete(self, key: str):
        """删除缓存"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"删除缓存: {key}")

    def clear(self):
        """清空所有缓存"""
        for f in self.cache_dir.glob("*.pkl"):
            f.unlink()
        logger.info("缓存已清空")