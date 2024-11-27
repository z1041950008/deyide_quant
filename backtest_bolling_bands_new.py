from tasks.boll_screener import BollScreener
from tasks.backtest import Backtest
import traceback

def main():
    # 使用示例
    strategy = BollScreener(include_cyb=False, include_kcb=False, top_n=10)
    backtest = Backtest(
        strategy=strategy,
        initial_capital=1000000,
        position_size=0.3
    )
    
    try:
        backtest.run(
            start_date='2024-11-01',
            end_date='2024-11-22'
        )
        print("回测完成")
    except Exception as e:
        print(f"回测失败: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
