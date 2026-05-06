import json
import time
import signal
import sys
import winreg
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Ensure parent project directory is on sys.path so imports work after moving this script.
key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, "PYPlugins", "user"))

from tqcenter import tq
from dingtalk_send import send_dingtalk

# ======================
# 配置参数
# ======================
# 监控的板块名称列表（通达信板块）
SECTOR_NAMES = ['ZXG']
# 涨幅阈值（%），超过此值触发预警
PRICE_RISE_THRESHOLD = 3.0
# 防抖间隔（秒），同一股票在该时间段内只触发一次预警
ANTI_SHAKE_SECONDS = 10
# 分批订阅大小，单次订阅的股票数量上限
BATCH_SUBSCRIBE_SIZE = 50

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
            # 获取板块股票列表，自选股使用内置代码ZXG，block_type=1
            sector_codes = tq.get_stock_list_in_sector(sector, block_type=1, list_type=0)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取板块{sector}股票列表：{len(sector_codes)}只股票")
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
            # 订阅实时行情，callback参数传入回调函数对象
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
    """取消所有股票的行情订阅
    
    程序退出时调用，批量取消订阅，释放TDX资源。
    """
    if SUBSCRIBE_CODES:
        try:
            tq.unsubscribe_hq(stock_list=SUBSCRIBE_CODES)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 已取消所有订阅")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 取消所有订阅失败：{e}")

def on_data(data_str):
    """实时行情回调函数（核心策略逻辑）
    
    TDX推送实时行情数据时自动调用此函数，执行涨幅监控和预警逻辑。
    数据以JSON字符串形式传入，需要先解析为字典。
    
    策略逻辑：
    1. 过滤已退出程序的数据
    2. 解析JSON数据，提取股票代码
    3. 过滤已触发预警的股票（单只股票只预警一次）
    4. 防抖过滤：10秒内同一股票不重复预警
    5. 获取实时快照（现价、前收、成交量）
    6. 计算涨幅：(现价 - 前收) / 前收 * 100
    7. 若涨幅超过阈值，触发预警并取消该股票订阅
    
    Args:
        data_str: TDX推送的JSON格式行情数据字符串
    
    Returns:
        None
    """
    global EXIT_FLAG
    if EXIT_FLAG:
        return None

    try:
        # 解析JSON格式的行情数据
        datas = json.loads(data_str)
        code = datas.get('Code', '')
        if not code:
            return None

        # 过滤：已触发预警的股票不再处理（单次触发策略）
        if code in TRIGGERED_STOCKS:
            return None

        # 获取当前时间戳（秒）
        now = time.time()
        # 过滤：防抖检查，10秒内不重复预警
        if now - last_warn_time[code] < ANTI_SHAKE_SECONDS:
            return None

        # 获取实时快照数据（包含现价、前收、成交量等）
        snapshot = tq.get_market_snapshot(stock_code=code)
        if not snapshot:
            return None

        # 解析现价和前收盘价
        latest_price = float(snapshot.get('Now', '0'))
        pre_close = float(snapshot.get('LastClose', '0'))

        # 过滤：前收盘价为0的数据（无效数据）
        if pre_close == 0:
            return None

        # 计算涨幅百分比（核心策略指标）
        rise_pct = (latest_price - pre_close) / pre_close * 100

        # 策略触发条件：涨幅超过阈值
        if rise_pct > PRICE_RISE_THRESHOLD:
            # 记录本次预警时间（防抖）
            last_warn_time[code] = now
            # 加入已触发集合（单次触发）
            TRIGGERED_STOCKS.add(code)
            # 取消该股票订阅，避免重复接收（资源优化）
            unsubscribe_single_stock(code)

            # 构造预警时间戳
            warn_time = datetime.now().strftime("%Y%m%d%H%M%S")
            # 预警原因
            reason = f"涨幅突破 {rise_pct:.2f}%"
            # 成交量
            volume = snapshot.get('Volume', '0')

            try:
                # 发送通达信预警信号
                # warn_type='3' 表示涨幅预警
                # bs_flag='0' 表示不区分买卖
                warn_res = tq.send_warn(
                    stock_list=[code],
                    time_list=[warn_time],
                    price_list=[str(latest_price)],
                    close_list=[str(pre_close)],
                    volum_list=[volume],
                    bs_flag_list=['0'],
                    warn_type_list=['3'],
                    reason_list=[reason],
                    count=1
                )
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 涨幅 {rise_pct:.2f}%，预警发送结果：{warn_res}")

                # 发送钉钉通知
                ding_msg = f"涨幅预警: {code}\n涨幅: {rise_pct:.2f}%\n现价: {latest_price}\n前收: {pre_close}\n原因: {reason}"
                send_dingtalk(ding_msg)
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 发送预警失败：{e}")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 回调函数执行异常：{e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 注册信号处理器，用于捕获 Ctrl+C 实现优雅退出
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 初始化TDX量化接口，__file__作为工作路径标识
        tq.initialize(str(Path(__file__).resolve().parents[1] / "test_api.py"))
        print(f"程序启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"TDX初始化成功")
        # 钉钉通知：系统启动
        send_dingtalk("系统通知: 实时涨幅预警已启动")
    except Exception as e:
        print(f"TDX初始化失败：{e}")
        exit(1)

    # 获取监控板块的有效股票代码
    print("获取所有板块列表...")
    all_sectors = tq.get_sector_list(list_type=0)
    print(f"所有板块：{all_sectors}")
    user_sectors = tq.get_user_sector()
    print(f"用户自定义板块：{user_sectors}")
    SUBSCRIBE_CODES = get_valid_stock_codes(SECTOR_NAMES)
    if not SUBSCRIBE_CODES:
        print("未获取到任何有效股票代码，程序退出")
        exit(1)

    # 批量订阅股票实时行情
    subscribe_stocks()

    # 打印监控配置信息
    print(f"\n=== 涨幅监控启动 ===")
    print(f"监控板块：{SECTOR_NAMES}")
    print(f"监控股票总数：{len(SUBSCRIBE_CODES)}")
    print(f"涨幅阈值：>{PRICE_RISE_THRESHOLD}%")
    print(f"防抖间隔：{ANTI_SHAKE_SECONDS}秒")
    print(f"分批订阅大小：{BATCH_SUBSCRIBE_SIZE}只/批")
    print("按 Ctrl+C 退出程序...\n")

    try:
        # 主循环：保持程序运行，等待退出信号
        # 通过0.1秒轮询检查EXIT_FLAG，实现快速响应
        while not EXIT_FLAG:
            time.sleep(0.1)
    except Exception as e:
        print(f"主循环异常：{e}")

    # 程序退出：取消所有股票订阅，释放TDX资源
    unsubscribe_stocks()
    print("程序已退出")