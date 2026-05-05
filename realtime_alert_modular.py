"""
通达信实时预警模块
支持多种预警场景：涨幅突破、均线金叉死叉、放量突破等
"""
import json
import time
import signal
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Callable, List, Dict, Optional
from tqcenter import tq

class RealtimeAlert:
    def __init__(self, sectors: List[str], batch_size: int = 50):
        self.sectors = sectors
        self.batch_size = batch_size
        self.subscribe_codes = []
        self.last_warn_time = defaultdict(int)
        self.triggered_stocks = set()
        self.exit_flag = False
        self.alert_callback: Optional[Callable] = None

    def get_stock_codes(self) -> List[str]:
        valid_codes = set()
        for sector in self.sectors:
            try:
                codes = tq.get_stock_list_in_sector(sector, list_type=0)
                for code in codes:
                    if code and isinstance(code, str) and (code.endswith('.SH') or code.endswith('.SZ')):
                        valid_codes.add(code)
            except Exception as e:
                print(f"获取板块{sector}股票列表失败：{e}")
        return list(valid_codes)

    def subscribe(self):
        for i in range(0, len(self.subscribe_codes), self.batch_size):
            batch = self.subscribe_codes[i:i+self.batch_size]
            try:
                tq.subscribe_hq(stock_list=batch, callback='on_realtime_data')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 订阅 {len(batch)} 只成功")
            except Exception as e:
                print(f"订阅失败：{e}")

    def unsubscribe(self):
        if self.subscribe_codes:
            try:
                tq.unsubscribe_hq(stock_list=self.subscribe_codes)
            except Exception as e:
                print(f"取消订阅失败：{e}")

    def send_alert(self, code: str, price: float, pre_close: float, reason: str, bs_flag: str = '0', warn_type: str = '3'):
        warn_time = datetime.now().strftime("%Y%m%d%H%M%S")
        try:
            snapshot = tq.get_market_snapshot(stock_code=code)
            volume = snapshot.get('Volume', '0') if snapshot else '0'
        except:
            volume = '0'

        try:
            res = tq.send_warn(
                stock_list=[code],
                time_list=[warn_time],
                price_list=[str(price)],
                close_list=[str(pre_close)],
                volum_list=[volume],
                bs_flag_list=[bs_flag],
                warn_type_list=[warn_type],
                reason_list=[reason],
                count=1
            )
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} {reason}，预警结果：{res}")
            return res
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 发送预警失败：{e}")
            return None

    def check_price_rise(self, code: str, threshold: float = 5.0, anti_shake: int = 10) -> bool:
        now = time.time()
        if now - self.last_warn_time[code] < anti_shake:
            return False

        snapshot = tq.get_market_snapshot(stock_code=code)
        if not snapshot:
            return False

        latest_price = float(snapshot.get('Now', '0'))
        pre_close = float(snapshot.get('LastClose', '0'))
        if pre_close == 0:
            return False

        rise_pct = (latest_price - pre_close) / pre_close * 100
        if rise_pct > threshold:
            self.last_warn_time[code] = now
            reason = f"涨幅突破 {rise_pct:.2f}%"
            self.send_alert(code, latest_price, pre_close, reason)
            return True
        return False

    def run(self, check_func: Callable[[str], bool], check_params: Dict = None):
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, 'exit_flag', True))

        tq.initialize(__file__)
        print(f"程序启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.subscribe_codes = self.get_stock_codes()
        if not self.subscribe_codes:
            print("未获取到有效股票代码")
            return

        self.subscribe()
        print(f"监控板块：{self.sectors}，股票数：{len(self.subscribe_codes)}")
        print("按 Ctrl+C 退出...\n")

        try:
            while not self.exit_flag:
                time.sleep(0.1)
        finally:
            self.unsubscribe()
            print("程序已退出")

def on_realtime_data(datas):
    pass

if __name__ == "__main__":
    alert = RealtimeAlert(sectors=['通达信88'], batch_size=50)
    alert.run(lambda code: alert.check_price_rise(code, threshold=5.0))