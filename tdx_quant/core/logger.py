"""
日志系统
"""
import logging
import sys
from pathlib import Path
from tdx_quant.config import LOG_CONFIG


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_CONFIG["level"]))

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(LOG_CONFIG["format"])
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 文件处理器
        try:
            file_handler = logging.FileHandler(LOG_CONFIG["file"], encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger