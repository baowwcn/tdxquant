"""
配置文件
"""

# 市场代码配置
MARKET_CONFIG = {
    "上证指数": "000001.SH",
    "深证成指": "399001.SZ",
    "创业板指": "399006.SZ",
    "科创50": "000688.SH",
    "沪深300": "000300.SH",
}

# 数据参数配置
DATA_CONFIG = {
    "default_period": "1d",  # 默认周期: 1m/5m/15m/30m/1h/1d/1w/1mon
    "default_dividend_type": "front",  # 复权类型: none/front/back
    "default_count": 500,  # 默认数据条数
    "cache_enabled": True,  # 是否启用缓存
}

# 策略参数配置
STRATEGY_CONFIG = {
    "name": "上证指数分析策略",
    "description": "基于缠论的指数分析策略",
    "fractal_n": 5,  # 分型确认需要的K线数量
    "bi_min_bars": 5,  # 笔的最少K线数
    "segment_min_bars": 9,  # 线段的最少K线数
}

# 交易参数配置（模拟）
TRADE_CONFIG = {
    "initial_cash": 1000000,  # 初始资金
    "max_position": 1.0,  # 最大持仓比例
    "commission_rate": 0.0003,  # 佣金费率
    "slippage": 0.001,  # 滑点
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "tdx_quant.log",
}