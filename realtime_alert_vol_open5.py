import json
import time
import signal
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from tqcenter import tq
from dingtalk_send import send_dingtalk

"""
实时成交量预警：开盘5分钟成交量大于昨日开盘5分钟成交量的1.1倍
基于 b_vol_open5.py 策略的实时版本

策略逻辑：
- 在交易日的9:30-9:35（开盘5分钟）内
- 若当日累计成交量（实时）超过昨日同期成交量的1.1倍
- 触发预警并发送通知

功能特点：
- 盘前预取昨日开盘5分钟成交量
- 实时跟踪当日开盘5分钟成交量
- 交易日自动切换，自动刷新昨日数据
- 防抖过滤、单股单次预警
- 支持通达信预警和钉钉通知
"""

# ======================
# 配置参数
# ======================
# 监控的板块名称列表（通达信板块）
SECTOR_NAMES = ['通达信88']
# 成交量倍数阈值，超过昨日开盘5分钟成交量的该倍数触发预警
VOLUME_RATIO_THRESHOLD = 1.1
# 防抖间隔（秒），同一股票在该时间段内只触发一次预警
ANTI_SHAKE_SECONDS = 10
# 分批订阅大小，单次订阅的股票数量上限
BATCH_SUBSCRIBE_SIZE = 50
# 开盘5分钟时间窗口（分钟）
OPEN5_WINDOW_MINUTES = 5
# 历史数据周期（天），用于获取昨日开盘5分钟数据
HISTORY_DAYS = 5

# ======================
# 全局状态变量
# ======================
# 待订阅的股票代码列表
SUBSCRIBE_CODES = []
# 上次预警时间记录，用于防抖过滤 {stock_code: timestamp}
last_warn_time = defaultdict(int)
# 程序退出标志位
EXIT_FLAG = False
# 已触发预警的股票集合，避免重复预警
TRIGGERED_STOCKS = set()
# 前一日开盘5分钟成交量缓存 {stock_code: volume}
prev_day_open5_volume = {}
# 当日开盘5分钟成交量累积 {stock_code: volume}
today_open5_volume = defaultdict(int)
# 当前交易日日期
current_trade_date = None

def signal_handler(sig, frame):
    """信号处理器 - 优雅退出
    
    捕获 Ctrl+C (SIGINT) 信号，设置退出标志位，
    确保主循环能够正常退出并执行资源清理。
    """
    global EXIT_FLAG
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到退出信号，正在清理...")
    EXIT_FLAG = True

def get_valid_stock_codes(sectors):
    """获取有效的股票代码列表
    
    从指定板块获取股票列表，并过滤出有效的A股代码（.SH/.SZ后缀）。
    
    Args:
        sectors: 板块名称列表
    
    Returns:
        有效的股票代码列表
    """
    valid_codes = set()
    for sector in sectors:
        try:
            # 获取板块股票列表，list_type=0 表示获取全部股票
            sector_codes = tq.get_stock_list_in_sector(sector, list_type=0)
            for code in sector_codes:
                # 过滤有效A股代码（沪市/深市）
                if code and isinstance(code, str) and (code.endswith('.SH') or code.endswith('.SZ')):
                    valid_codes.add(code)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取板块{sector}股票列表失败：{e}")
    return list(valid_codes)

def subscribe_stocks():
    """批量订阅股票实时行情
    
    将股票列表按批次拆分，通过TDX接口订阅实时行情数据。
    订阅成功后，TDX会推送实时数据到回调函数 on_data。
    """
    for i in range(0, len(SUBSCRIBE_CODES), BATCH_SUBSCRIBE_SIZE):
        batch = SUBSCRIBE_CODES[i:i+BATCH_SUBSCRIBE_SIZE]
        try:
            # 订阅实时行情，callback参数指定回调函数名称
            tq.subscribe_hq(stock_list=batch, callback=on_data)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 订阅 {len(batch)} 只股票成功")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 订阅失败：{e}")

def unsubscribe_single_stock(code):
    """取消单只股票的行情订阅
    
    当某只股票触发预警后，调用此函数取消订阅，避免重复接收该股票数据。
    
    Args:
        code: 要取消订阅的股票代码
    """
    try:
        tq.unsubscribe_hq(stock_list=[code])
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 取消订阅 {code} 失败：{e}")

def unsubscribe_stocks():
    """取消所有股票的行情订阅"""
    if SUBSCRIBE_CODES:
        try:
            tq.unsubscribe_hq(stock_list=SUBSCRIBE_CODES)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 已取消所有订阅")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 取消所有订阅失败：{e}")

def get_yesterday_open5_volume(stock_code: str) -> float:
    """
    获取指定股票昨日开盘5分钟成交量
    通过获取5分钟K线，取最近一个交易日的第一个bar的成交量
    """
    try:
        # 获取足够多的5分钟K线（覆盖最近5个交易日，一天48根）
        bars_needed = HISTORY_DAYS * 48 + 10
        df = tq.get_market_data(['Volume'], [stock_code], '5m', count=bars_needed)
        if 'Volume' not in df or stock_code not in df['Volume']:
            return 0.0
        vol_series = df['Volume'][stock_code]
        if len(vol_series) == 0:
            return 0.0
        # 按时间排序
        sorted_idx = sorted(vol_series.index)
        # 获取最后一个交易日的第一个bar
        last_date = None
        for ts in reversed(sorted_idx):
            date_str = str(ts).split()[0]
            if date_str != last_date:
                last_date = date_str
                return float(vol_series[ts])
        return 0.0
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取{stock_code}昨日开盘5分钟成交量失败：{e}")
        return 0.0

def is_within_open5_window() -> bool:
    """判断当前时间是否在开盘5分钟时间窗口内（9:30-9:35）"""
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    window_end = market_open + timedelta(minutes=OPEN5_WINDOW_MINUTES)
    return market_open <= now < window_end

def get_open5_window_end(stock_code: str, trade_date: str) -> datetime:
    """获取指定股票在某个交易日的开盘5分钟截止时间"""
    # 简单返回当天的9:35，实际交易中不同市场开盘时间相同
    return datetime.strptime(trade_date, "%Y-%m-%d").replace(hour=9, minute=35, second=0)

def reset_daily_cache():
    """每日开盘时重置缓存"""
    global today_open5_volume
    today_open5_volume.clear()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开盘缓存已重置")

def refresh_for_new_day(new_date: str):
    """
    交易日变更时刷新昨日数据
    """
    global prev_day_open5_volume, current_trade_date, SUBSCRIBE_CODES
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 检测到交易日变更，刷新昨日数据...")
    current_trade_date = new_date
    
    # 重置当日缓存
    reset_daily_cache()
    
    # 重新获取昨日开盘5分钟成交量
    new_volumes = prefetch_prev_day_volumes(SUBSCRIBE_CODES)
    
    # 更新全局缓存
    prev_day_open5_volume.clear()
    prev_day_open5_volume.update(new_volumes)
    
    # 过滤无效股票（昨日开盘5分钟成交量为0）
    invalid_codes = [code for code, vol in prev_day_open5_volume.items() if vol <= 0]
    for code in invalid_codes:
        if code in SUBSCRIBE_CODES:
            SUBSCRIBE_CODES.remove(code)
            print(f"  剔除股票 {code}: 昨日开盘5分钟成交量为0")
    
    print(f"刷新完成，有效监控股票：{len(SUBSCRIBE_CODES)}只")

def prefetch_prev_day_volumes(stock_codes: list) -> dict:
    """
    预获取所有股票的昨日开盘5分钟成交量
    返回：{stock_code: volume}
    """
    print("正在获取昨日开盘5分钟成交量数据...")
    volumes = {}
    for i, code in enumerate(stock_codes):
        vol = get_yesterday_open5_volume(code)
        volumes[code] = vol
        if (i + 1) % 20 == 0:
            print(f"  已获取 {i+1}/{len(stock_codes)} 只股票")
    print(f"昨日开盘5分钟成交量数据获取完成（共{len(volumes)}只）")
    return volumes

def check_volume_alert(stock_code: str, current_volume: float, prev_vol: float) -> tuple:
    """
    检查是否触发成交量预警
    返回：(是否触发, 倍数, 昨日成交量)
    """
    if prev_vol <= 0:
        return False, 0.0, prev_vol
    
    ratio = current_volume / prev_vol if prev_vol > 0 else 0.0
    
    if ratio > VOLUME_RATIO_THRESHOLD:
        return True, ratio, prev_vol
    return False, ratio, prev_vol

def on_data(data_str):
    """实时行情回调函数（成交量预警策略）"""
    global EXIT_FLAG, current_trade_date
    if EXIT_FLAG:
        return None

    try:
        # 1. 解析行情数据
        datas = json.loads(data_str)
        code = datas.get('Code', '')
        if not code:
            return None

        # 2. 过滤已触发预警的股票
        if code in TRIGGERED_STOCKS:
            return None

        # 3. 防抖过滤
        now_ts = time.time()
        if now_ts - last_warn_time[code] < ANTI_SHAKE_SECONDS:
            return None

        # 4. 获取实时快照
        snapshot = tq.get_market_snapshot(stock_code=code)
        if not snapshot:
            return None

        # 5. 获取当前成交量（手）并转换为股
        current_volume_lots = float(snapshot.get('Volume', '0'))
        current_volume = current_volume_lots * 100.0  # 转换为股，与5分钟K线单位一致
        if current_volume <= 0:
            return None

        now = datetime.now()
        current_time = now.strftime('%H:%M:%S')
        trade_date = now.strftime('%Y-%m-%d')

        # 6. 交易日变更检测
        if current_trade_date is None:
            current_trade_date = trade_date
        elif trade_date != current_trade_date:
            refresh_for_new_day(trade_date)

        # 7. 判断是否在开盘5分钟窗口内
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        window_end_time = market_open + timedelta(minutes=OPEN5_WINDOW_MINUTES)
        in_window = market_open <= now < window_end_time

        # 更新当日累计成交量
        today_open5_volume[code] = current_volume

        # 8. 只在开盘5分钟窗口内检查预警
        if in_window:
            prev_vol = prev_day_open5_volume.get(code, 0.0)
            triggered, ratio, _ = check_volume_alert(code, current_volume, prev_vol)

            if triggered:
                # 9. 触发预警
                last_warn_time[code] = now_ts
                TRIGGERED_STOCKS.add(code)
                unsubscribe_single_stock(code)

                # 构造预警信息
                warn_time = now.strftime("%Y%m%d%H%M%S")
                latest_price = float(snapshot.get('Now', '0'))
                pre_close = float(snapshot.get('LastClose', '0'))
                reason = f"开盘5分钟成交量达昨日{ratio:.2f}倍（阈值{VOLUME_RATIO_THRESHOLD}倍）"

                print(f"[{current_time}] {code} 触发成交量预警: {ratio:.2f}倍, 今日量:{current_volume/100:.0f}手, 昨日量:{prev_vol/100:.0f}手")

                try:
                    # 发送通达信预警信号
                    warn_res = tq.send_warn(
                        stock_list=[code],
                        time_list=[warn_time],
                        price_list=[str(latest_price)],
                        close_list=[str(pre_close)],
                        volum_list=[str(int(current_volume / 100))],  # 以手为单位
                        bs_flag_list=['0'],
                        warn_type_list=['3'],  # 使用类型3，原涨幅预警类型，可自定义
                        reason_list=[reason],
                        count=1
                    )
                    print(f"  通达信预警发送结果：{warn_res}")

                    # 发送钉钉通知
                    ding_msg = (
                        f"成交量预警: {code}\n"
                        f"倍数: {ratio:.2f}倍（阈值>{VOLUME_RATIO_THRESHOLD}倍）\n"
                        f"今日开盘5分钟成交量: {current_volume/100:.0f}手\n"
                        f"昨日开盘5分钟成交量: {prev_vol/100:.0f}手\n"
                        f"现价: {latest_price}\n"
                        f"原因: {reason}"
                    )
                    send_dingtalk(ding_msg)
                except Exception as e:
                    print(f"[{current_time}] {code} 发送预警失败：{e}")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 回调函数执行异常：{e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 注册信号处理器，用于捕获 Ctrl+C 实现优雅退出
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 初始化TDX量化接口
        tq.initialize(__file__)
        print(f"程序启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"TDX初始化成功")
        # 钉钉通知：系统启动
        send_dingtalk("系统通知: 实时成交量预警已启动（开盘5分钟>1.1倍策略）")
    except Exception as e:
        print(f"TDX初始化失败：{e}")
        exit(1)

    # 获取监控板块的有效股票代码
    SUBSCRIBE_CODES = get_valid_stock_codes(SECTOR_NAMES)
    if not SUBSCRIBE_CODES:
        print("未获取到任何有效股票代码，程序退出")
        exit(1)

    # 预获取昨日开盘5分钟成交量
    prev_day_open5_volume = prefetch_prev_day_volumes(SUBSCRIBE_CODES)

    # 过滤掉昨日开盘5分钟成交量为0的股票（数据异常）
    valid_codes = [code for code in SUBSCRIBE_CODES if prev_day_open5_volume.get(code, 0) > 0]
    print(f"有效股票数量（有昨日数据）: {len(valid_codes)}/{len(SUBSCRIBE_CODES)}")
    SUBSCRIBE_CODES = valid_codes

    # 重置当日缓存
    reset_daily_cache()

    # 批量订阅股票实时行情
    subscribe_stocks()

    # 打印监控配置信息
    print(f"\n=== 成交量监控启动 ===")
    print(f"监控板块：{SECTOR_NAMES}")
    print(f"监控股票总数：{len(SUBSCRIBE_CODES)}")
    print(f"策略：开盘5分钟成交量 > 昨日开盘5分钟成交量 × {VOLUME_RATIO_THRESHOLD}")
    print(f"防抖间隔：{ANTI_SHAKE_SECONDS}秒")
    print(f"分批订阅大小：{BATCH_SUBSCRIBE_SIZE}只/批")
    print("按 Ctrl+C 退出程序...\n")

    try:
        # 主循环：保持程序运行，等待退出信号
        while not EXIT_FLAG:
            time.sleep(0.1)
    except Exception as e:
        print(f"主循环异常：{e}")

    # 程序退出：取消所有股票订阅，释放TDX资源
    unsubscribe_stocks()
    print("程序已退出")