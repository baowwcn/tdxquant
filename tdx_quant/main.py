"""
程序入口 - 上证指数量化分析（严格缠论版）
"""
import sys
sys.path.insert(0, r"D:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
from tdx_quant.strategy.index_strategy import IndexStrategy
from tdx_quant.signal.strategy_signal import print_chan_signal, get_strict_signal
from tdx_quant.config import MARKET_CONFIG


def main():
    """主函数"""
    print("=" * 60)
    print("  上证指数量化分析系统（严格缠论版）")
    print("=" * 60)

    tq.initialize(__file__)

    strategy = IndexStrategy(index_code=MARKET_CONFIG["上证指数"])
    strategy.load_data(count=500, period="1d")

    strategy.print_analysis()

    print("\n")
    print_chan_signal(strategy.history_data)

    # 严格版信号
    signal_result = get_strict_signal(strategy.history_data)

    print("\n" + "=" * 60)
    print("  严格版交易信号")
    print("=" * 60)
    print(f"  信号: {signal_result.get('signal', 'N/A')}")
    print(f"  理由: {signal_result.get('reason', [])}")

    if signal_result.get("last_confirmed_bi"):
        lb = signal_result["last_confirmed_bi"]
        print(f"\n  最近已确认笔:")
        print(f"    方向: {'上涨' if lb.direction == 'up' else '下跌'}")
        print(f"    幅度: {lb.length:.2f}")

    print("=" * 60)

    tq.close()
    print("\n完成!")


if __name__ == "__main__":
    main()