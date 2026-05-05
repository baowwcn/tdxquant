import json
import time
import signal
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from tqcenter import tq
from dingtalk_send import send_dingtalk

SECTOR_NAMES = ['通达信88']
PRICE_RISE_THRESHOLD = 5.0
ANTI_SHAKE_SECONDS = 10
BATCH_SUBSCRIBE_SIZE = 50

SUBSCRIBE_CODES = []
last_warn_time = defaultdict(int)
EXIT_FLAG = False
TRIGGERED_STOCKS = set()

def signal_handler(sig, frame):
    global EXIT_FLAG
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到退出信号，正在清理...")
    EXIT_FLAG = True

def get_valid_stock_codes(sectors):
    valid_codes = set()
    for sector in sectors:
        try:
            sector_codes = tq.get_stock_list_in_sector(sector, list_type=0)
            for code in sector_codes:
                if code and isinstance(code, str) and (code.endswith('.SH') or code.endswith('.SZ')):
                    valid_codes.add(code)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取板块{sector}股票列表失败：{e}")
    return list(valid_codes)

def subscribe_stocks():
    for i in range(0, len(SUBSCRIBE_CODES), BATCH_SUBSCRIBE_SIZE):
        batch = SUBSCRIBE_CODES[i:i+BATCH_SUBSCRIBE_SIZE]
        try:
            tq.subscribe_hq(stock_list=batch, callback='on_data')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 订阅 {len(batch)} 只股票成功")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 订阅失败：{e}")

def unsubscribe_single_stock(code):
    try:
        tq.unsubscribe_hq(stock_list=[code])
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 取消订阅 {code} 失败：{e}")

def unsubscribe_stocks():
    if SUBSCRIBE_CODES:
        try:
            tq.unsubscribe_hq(stock_list=SUBSCRIBE_CODES)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 已取消所有订阅")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 取消所有订阅失败：{e}")

def on_data(datas):
    global EXIT_FLAG
    if EXIT_FLAG:
        return None

    try:
        code = datas.get('Code', '')
        if not code:
            return None

        if code in TRIGGERED_STOCKS:
            return None

        now = time.time()
        if now - last_warn_time[code] < ANTI_SHAKE_SECONDS:
            return None

        snapshot = tq.get_market_snapshot(stock_code=code)
        if not snapshot:
            return None

        latest_price = float(snapshot.get('Now', '0'))
        pre_close = float(snapshot.get('LastClose', '0'))

        if pre_close == 0:
            return None

        rise_pct = (latest_price - pre_close) / pre_close * 100

        if rise_pct > PRICE_RISE_THRESHOLD:
            last_warn_time[code] = now
            TRIGGERED_STOCKS.add(code)
            unsubscribe_single_stock(code)

            warn_time = datetime.now().strftime("%Y%m%d%H%M%S")
            reason = f"涨幅突破 {rise_pct:.2f}%"
            volume = snapshot.get('Volume', '0')

            try:
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
    signal.signal(signal.SIGINT, signal_handler)

    try:
        tq.initialize(__file__)
        print(f"程序启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"TDX初始化成功")
        send_dingtalk("系统通知: 实时涨幅预警已启动")
    except Exception as e:
        print(f"TDX初始化失败：{e}")
        exit(1)

    SUBSCRIBE_CODES = get_valid_stock_codes(SECTOR_NAMES)
    if not SUBSCRIBE_CODES:
        print("未获取到任何有效股票代码，程序退出")
        exit(1)

    subscribe_stocks()

    print(f"\n=== 涨幅监控启动 ===")
    print(f"监控板块：{SECTOR_NAMES}")
    print(f"监控股票总数：{len(SUBSCRIBE_CODES)}")
    print(f"涨幅阈值：>{PRICE_RISE_THRESHOLD}%")
    print(f"防抖间隔：{ANTI_SHAKE_SECONDS}秒")
    print(f"分批订阅大小：{BATCH_SUBSCRIBE_SIZE}只/批")
    print("按 Ctrl+C 退出程序...\n")

    try:
        while not EXIT_FLAG:
            time.sleep(0.1)
    except Exception as e:
        print(f"主循环异常：{e}")

    unsubscribe_stocks()
    print("程序已退出")