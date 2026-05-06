"""
量化回测：开盘5分钟成交量大于昨天开盘5分钟成交量的股票，3天内收益5%以上
修正版：
1. 修复5分钟K线数量不足问题（一天48根，取足够天数）
2. 以第一个5分钟K线的收盘价作为买入价（更贴近实际信号确认点）
3. 加入停牌/无效价格过滤
4. 优化异常处理与日志输出
"""

import sys
sys.path.insert(0, 'C:/new_tdx64/PYPlugins/user')
from tqcenter import tq
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

tq.initialize('dummy.py')

def get_open5min_data(stock_code: str, days: int = 60) -> Tuple[Optional[Dict[str, float]], Optional[Dict[str, float]]]:
    """
    获取股票每日开盘5分钟（第一个5分钟bar）的成交量和收盘价
    返回: (成交量字典{日期:成交量}, 价格字典{日期:收盘价})，日期格式YYYY-MM-DD
    """
    try:
        # 一天有48根5分钟K线，额外多取5天避免边界缺失
        bars_needed = days * 48 + 5 * 48
        df = tq.get_market_data(['Volume', 'Close'], [stock_code], '5m', count=bars_needed)
        if 'Volume' not in df or stock_code not in df['Volume']:
            return None, None
        vol_series = df['Volume'][stock_code]
        close_series = df['Close'][stock_code] if 'Close' in df and stock_code in df['Close'] else None
        
        vol_dict = {}
        price_dict = {}
        # 每个交易日只取第一个5分钟bar
        last_date = None
        for ts in sorted(vol_series.index):
            date_str = str(ts).split()[0]
            if date_str != last_date:
                vol_dict[date_str] = float(vol_series[ts])
                if close_series is not None:
                    price_dict[date_str] = float(close_series[ts])
                last_date = date_str
        return vol_dict, price_dict
    except Exception as e:
        print(f"获取{stock_code}5分钟数据出错: {e}")
        return None, None

def get_daily_close(stock_code: str, count: int = 200) -> Optional[Dict[str, float]]:
    """获取日线收盘价字典，过滤停牌日（价格为0或NaN）"""
    try:
        df = tq.get_market_data(['Close'], [stock_code], '1d', count=count)
        if 'Close' not in df or stock_code not in df['Close']:
            return None
        close = df['Close'][stock_code]
        result = {}
        for d, v in zip(close.index, close.values):
            date_str = str(d).split()[0]
            if pd.notna(v) and v > 0:
                result[date_str] = float(v)
        return result
    except Exception as e:
        print(f"获取{stock_code}日线收盘价出错: {e}")
        return None

def run_backtest(stock_code: str, 
                 open5_vol: Dict[str, float],
                 open5_price: Dict[str, float],
                 close_prices: Dict[str, float],
                 hold_days: int = 3,
                 volume_ratio: float = 1.1) -> List[Dict]:
    """
    执行回测
    - 信号日: 当日开盘5分钟成交量 > 昨日 * volume_ratio
    - 买入价: 当日第一个5分钟K线收盘价（open5_price）
    - 卖出日: hold_days个交易日后
    - 卖出价: 该日收盘价
    """
    trades = []
    # 取三者的共同日期并排序
    common_dates = sorted(set(open5_vol.keys()) & set(open5_price.keys()) & set(close_prices.keys()))
    if len(common_dates) < hold_days + 1:
        return trades
    
    for i in range(1, len(common_dates) - hold_days):
        curr_date = common_dates[i]
        prev_date = common_dates[i-1]
        
        # 成交量条件
        if open5_vol[curr_date] > open5_vol[prev_date] * volume_ratio:
            entry_price = open5_price[curr_date]      # 第一个5分钟K收盘价
            exit_date = common_dates[i+hold_days]
            exit_price = close_prices[exit_date]
            
            # 有效价格检查
            if entry_price <= 0 or exit_price <= 0:
                continue
                
            ret = (exit_price - entry_price) / entry_price
            trades.append({
                'stock': stock_code,
                'entry_date': curr_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'ret': ret
            })
    return trades

def main():
    print("获取股票列表...")
    # 获取全部A股（市场代码0:深圳,1:上海,可根据需要调整）
    stocks = tq.get_stock_list(market='0', list_type=0) + tq.get_stock_list(market='1', list_type=0)
    # 过滤并取前100支用于演示（可自行修改）
    stocks = [s for s in stocks if s.startswith(('0','3','6'))][:100]
    print(f"待测股票数量: {len(stocks)}")
    
    all_trades = []
    stock_trades_count = {}
    
    for i, stock in enumerate(stocks):
        print(f"[{i+1}/{len(stocks)}] 处理 {stock}...")
        
        # 获取开盘5分钟量价数据（60个交易日）
        vol_dict, price_dict = get_open5min_data(stock, days=60)
        if not vol_dict or not price_dict:
            print(f"  [跳过] {stock} 5分钟数据不足")
            continue
        
        # 获取日线收盘价（200个交易日）
        close_dict = get_daily_close(stock, count=200)
        if not close_dict or len(close_dict) < 10:
            print(f"  ⚠️ {stock} 日线数据不足，跳过")
            continue
        
        # 执行回测
        trades = run_backtest(stock, vol_dict, price_dict, close_dict, hold_days=3, volume_ratio=1.1)
        if trades:
            all_trades.extend(trades)
            stock_trades_count[stock] = len(trades)
            print(f"  [信号] 产生 {len(trades)} 个交易信号")
        else:
            print(f"  [无信号]")
    
    # 输出汇总结果
    print("\n" + "="*60)
    print("回测结果汇总")
    print("="*60)
    
    if all_trades:
        returns = [t['ret'] for t in all_trades]
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        print(f"总交易次数: {len(all_trades)}")
        print(f"胜率: {win_rate:.2%}")
        print(f"平均收益率: {np.mean(returns):.2%}")
        print(f"中位数收益率: {np.median(returns):.2%}")
        print(f"最大收益率: {max(returns):.2%}")
        print(f"最小收益率: {min(returns):.2%}")
        
        # 按股票统计
        print("\n按股票统计:")
        for stock, cnt in stock_trades_count.items():
            stock_ret = [t['ret'] for t in all_trades if t['stock'] == stock]
            print(f"  {stock}: 信号{cnt}次, 平均收益{np.mean(stock_ret):.2%}")
        
        # 输出前10笔盈利最多的交易
        df = pd.DataFrame(all_trades).sort_values('ret', ascending=False)
        print("\n收益前10的交易记录:")
        print(df.head(10).to_string(index=False))
        
        # 保存结果到CSV
        df.to_csv('backtest_result.csv', index=False, encoding='utf-8-sig')
        print("\n完整交易记录已保存至 backtest_result.csv")
    else:
        print("没有产生任何交易信号，请检查数据或调整参数。")
        # 可选：输出少量股票的详细数据用于调试
        print("\n调试信息（前5支股票的开盘5分钟量数据样本）:")
        for stock in stocks[:5]:
            vol_dict, _ = get_open5min_data(stock, days=10)
            if vol_dict:
                print(f"{stock}: {list(vol_dict.items())[:3]} ... 共{len(vol_dict)}天")
            else:
                print(f"{stock}: 无数据")

if __name__ == '__main__':
    main()