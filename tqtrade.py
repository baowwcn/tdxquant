"""
通达信交易封装 - 完整示例
基于 tdxquant (tqcenter.py) 提供交易接口
使用前确保:
  1. 通达信客户端已登录交易系统
  2. tqcenter.py 及 TPythClient.dll 可用
操作流程:
  1. 初始化连接 → 获取交易账户句柄
  2. 查询账户资产 / 持仓 / 委托
  3. 买卖下单 / 撤单
  4. 获取实时行情
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq, tqconst

def _f(val):
    """安全转 float，兼容字符串/数字/None"""
    try:
        return float(val) if val not in (None, "", "None") else 0.0
    except (TypeError, ValueError):
        return 0.0

def _i(val):
    """安全转 int"""
    try:
        return int(val) if val not in (None, "", "None") else 0
    except (TypeError, ValueError):
        return 0

STATUS_MAP = {
    0: "无效单",
    1: "未成交",
    2: "部分成交",
    3: "全部成交",
    4: "部分撤单",
    5: "全部撤单",
}

def _status_text(code):
    """委托状态码转文字"""
    if code is None:
        return "未知"
    try:
        return STATUS_MAP.get(int(code), f"状态{code}")
    except (TypeError, ValueError):
        return str(code)

def init_tdx(tdx_path: str = ""):
    """初始化 TQ 连接"""
    path = tdx_path or __file__
    try:
        tq.initialize(path)
        print(f"[OK] TQ 初始化成功，连接路径: {path}")
        return True
    except Exception as e:
        print(f"[ERROR] TQ 初始化失败: {e}")
        return False

def get_account(account: str = "", account_type: str = "stock") -> int:
    """获取交易账户句柄"""
    acc = tq.stock_account(account=account, account_type=account_type)
    if acc < 0:
        print("[ERROR] 获取账户句柄失败，请确认通达信已登录交易系统")
        return -1
    print(f"[OK] 账户句柄: {acc}")
    return acc

def query_asset(account_id: int) -> Dict:
    """查询账户资产信息"""
    data = tq.query_stock_asset(account_id=account_id)
    if not data:
        print("[WARN] 未获取到资产信息")
        return {}
    print("\n" + "=" * 50)
    print("  账户资产")
    print("=" * 50)
    v = data.get("Value", data)
    if isinstance(v, dict):
        for key, value in v.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {data}")
    print("=" * 50)
    return data

def query_positions(account_id: int) -> List[Dict]:
    """查询当前持仓"""
    positions = tq.query_stock_positions(account_id=account_id) or []
    if not positions:
        print("[INFO] 当前无持仓")
        return []
    print(f"\n[OK] 当前共 {len(positions)} 只持仓:")
    print("-" * 90)
    headers = list(positions[0].keys())
    print("  " + " | ".join([str(h).ljust(14) for h in headers]))
    print("-" * 90)
    for pos in positions:
        print("  " + " | ".join([str(pos.get(h, "")).ljust(14) for h in headers]))
    print("-" * 90)
    total = 0.0
    for pos in positions:
        total += _f(pos.get("Zjz", pos.get("MarketValue", 0)))
    if total > 0:
        print(f"\n  持仓总市值: {total:,.2f} 元")
    return positions

def query_orders(account_id: int, stock_code: str = "") -> List[Dict]:
    """查询当日委托"""
    orders = tq.query_stock_orders(account_id=account_id, stock_code=stock_code) or []
    if not orders:
        print("[INFO] 当日无委托")
        return []
    print(f"\n[OK] 当日共 {len(orders)} 笔委托:")
    print("-" * 90)
    headers = list(orders[0].keys())
    print("  " + " | ".join([str(h).ljust(12) for h in headers]))
    print("-" * 90)
    for order in orders:
        print("  " + " | ".join([str(order.get(h, "")).ljust(12) for h in headers]))
    print("-" * 90)
    status_count = {}
    for order in orders:
        s = _status_text(order.get("Wtzt", "未知"))
        status_count[s] = status_count.get(s, 0) + 1
    if status_count:
        print("\n  委托状态统计:")
        for s, c in status_count.items():
            print(f"    {s}: {c} 笔")
    return orders

def get_quote(stock_code: str) -> Dict:
    """获取单只股票实时行情"""
    data = tq.get_market_snapshot(stock_code=stock_code)
    if not data or data.get("ErrorId", "0") != "0":
        print(f"[WARN] 获取 {stock_code} 行情失败")
        return {}
    return data

def print_quote(stock_code: str):
    """格式化打印行情"""
    q = get_quote(stock_code)
    if not q:
        return
    info = tq.get_stock_info(stock_code=stock_code)
    name = info.get("Name", info.get("StockName", stock_code))
    price = _f(q.get("Now", 0))
    last_close = _f(q.get("LastClose", 0))
    change = price - last_close
    change_pct = change / last_close * 100 if last_close > 0 else 0
    sign = "+" if change >= 0 else ""
    buyp = q.get("Buyp", [])
    buyv = q.get("Buyv", [])
    sellp = q.get("Sellp", [])
    sellv = q.get("Sellv", [])
    print(f"\n{'='*45}")
    print(f"  {name} ({stock_code})")
    print(f"  现价: {price:.2f}  {sign}{change:.2f} ({sign}{change_pct:.2f}%)")
    print(f"  开盘: {_f(q.get('Open')):.2f}  最高: {_f(q.get('Max')):.2f}")
    print(f"  最低: {_f(q.get('Min')):.2f}  昨收: {last_close:.2f}")
    print(f"  均价: {_f(q.get('Average')):.2f}  成交量: {q.get('Volume', 0)}手  成交额: {q.get('Amount', 0)}万")
    print(f"  内盘: {q.get('Inside', 0)}  外盘: {q.get('Outside', 0)}")
    print(f"  ---- 买盘 ----")
    for i in range(min(5, len(buyp))):
        print(f"  买{i+1}: {buyp[i]:>8s} x {buyv[i]:>6s}")
    print(f"  ---- 卖盘 ----")
    for i in range(min(5, len(sellp))):
        print(f"  卖{i+1}: {sellp[i]:>8s} x {sellv[i]:>6s}")
    print(f"{'='*45}")

def order_buy(account_id: int, stock_code: str, price: float, volume: int,
              price_type: int = 0, notify: int = 1) -> Dict:
    """买入下单"""
    print(f"\n>>> 买入委托: {stock_code}  价格={price}  数量={volume}")
    result = tq.order_stock(
        account_id=account_id,
        stock_code=stock_code,
        order_type=tqconst.STOCK_BUY,
        order_volume=volume,
        price_type=price_type,
        price=price,
        notify=notify
    )
    if result == -1 or result is None:
        print(f"[ERROR] 买入委托失败")
        return {}
    if result.get("ErrorId", "0") != "0":
        print(f"[ERROR] 买入失败: {result}")
        return {}
    print(f"[OK] 买入委托成功: {result}")
    return result

def order_sell(account_id: int, stock_code: str, price: float, volume: int,
               price_type: int = 0, notify: int = 1) -> Dict:
    """卖出下单"""
    print(f"\n>>> 卖出委托: {stock_code}  价格={price}  数量={volume}")
    result = tq.order_stock(
        account_id=account_id,
        stock_code=stock_code,
        order_type=tqconst.STOCK_SELL,
        order_volume=volume,
        price_type=price_type,
        price=price,
        notify=notify
    )
    if result == -1 or result is None:
        print(f"[ERROR] 卖出委托失败")
        return {}
    if result.get("ErrorId", "0") != "0":
        print(f"[ERROR] 卖出失败: {result}")
        return {}
    print(f"[OK] 卖出委托成功: {result}")
    return result

def order_buy_market(account_id: int, stock_code: str, volume: int, notify: int = 1) -> Dict:
    """市价买入"""
    return order_buy(account_id, stock_code, price=0, volume=volume,
                     price_type=tqconst.PRICE_SJ, notify=notify)

def order_sell_market(account_id: int, stock_code: str, volume: int, notify: int = 1) -> Dict:
    """市价卖出"""
    return order_sell(account_id, stock_code, price=0, volume=volume,
                      price_type=tqconst.PRICE_SJ, notify=notify)

def order_cancel(account_id: int, order_id: str, stock_code: str = "") -> Dict:
    """撤单"""
    print(f"\n>>> 撤单: {order_id}")
    result = tq.cancel_order_stock(
        account_id=account_id,
        stock_code=stock_code,
        order_id=order_id
    )
    if result == -1 or result is None:
        print(f"[ERROR] 撤单失败")
        return {}
    print(f"[OK] 撤单成功: {result}")
    return result

def query_position_by_code(account_id: int, stock_code: str) -> Optional[Dict]:
    """查询指定股票的持仓"""
    positions = tq.query_stock_positions(account_id=account_id) or []
    for pos in positions:
        code = pos.get("Code", pos.get("Zqdm", pos.get("StockCode", "")))
        if code == stock_code:
            print(f"\n[OK] {stock_code} 持仓信息:")
            for k, v in pos.items():
                print(f"  {k}: {v}")
            return pos
    print(f"[INFO] 未持有 {stock_code}")
    return None

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  通达信交易程序 启动")
    print("=" * 60)
    if not init_tdx():
        exit(1)

    print("\n【步骤1】获取交易账户句柄...")
    myAccount = get_account(account="", account_type="stock")
    if myAccount < 0:
        tq.close()
        exit(1)

    print("\n【步骤2】查询账户资产...")
    query_asset(myAccount)

    print("\n【步骤3】查询持仓...")
    positions = query_positions(myAccount)

    print("\n【步骤4】查询当日委托...")
    query_orders(myAccount)

    print("\n【步骤5】查询中际旭创(300308.SZ)持仓...")
    query_position_by_code(myAccount, "300308.SZ")

    print("\n【步骤6】获取中际旭创(300308.SZ)实时行情...")
    print_quote("300308.SZ")

    print("\n【步骤7】买入中际旭创 100股 @ 919.99...")
    BUY_ENABLED = True
    if BUY_ENABLED:
        buy_result = order_buy(
            account_id=myAccount,
            stock_code="300308.SZ",
            price=919.99,
            volume=100,
            notify=1
        )
        if buy_result:
            print(f"  买入结果: {json.dumps(buy_result, ensure_ascii=False, indent=2)}")
    else:
        print("  (买入已跳过，将 BUY_ENABLED 改为 True 可执行)")

    print("\n【步骤8】卖出中际旭创 100股 @ 919.99...")
    SELL_ENABLED = True
    if SELL_ENABLED:
        sell_result = order_sell(
            account_id=myAccount,
            stock_code="300308.SZ",
            price=919.99,
            volume=100,
            notify=1
        )
        if sell_result:
            print(f"  卖出结果: {json.dumps(sell_result, ensure_ascii=False, indent=2)}")
    else:
        print("  (卖出已跳过，将 SELL_ENABLED 改为 True 可执行)")

    if BUY_ENABLED or SELL_ENABLED:
        print("\n【步骤9】下单后再次查询持仓和委托...")
        query_positions(myAccount)
        query_orders(myAccount)

    print("\n" + "=" * 60)
    tq.close()
    print("  连接已关闭，程序结束")
    print("=" * 60)