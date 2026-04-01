"""
get_stock_data.py - 获取股票数据示例
使用 akshare 获取 A 股历史行情
"""
import pandas as pd
import akshare as ak
from datetime import datetime

def get_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取 A 股历史行情数据
    
    参数:
        symbol: 股票代码，如 '000001'
        start_date: 开始日期，格式 'YYYYMMDD'
        end_date: 结束日期，格式 'YYYYMMDD'
    
    返回:
        DataFrame 包含股票行情数据
    """
    try:
        # 使用 akshare 获取个股历史行情
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        
        # 重命名列
        df.columns = [
            'date', 'open', 'close', 'high', 'low',
            'volume', 'turnover', 'amplitude', 'pct_change',
            'change', 'turnover_rate'
        ]
        
        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    except Exception as e:
        print(f"获取数据失败：{e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # 获取平安银行 2023 年数据
    print("正在获取股票数据...")
    df = get_stock_data("000001", "20230101", "20231231")
    
    if not df.empty:
        print(f"\n✅ 成功获取 {len(df)} 条数据")
        print("\n前 5 行数据:")
        print(df.head())
        print("\n数据描述:")
        print(df.describe())
        
        # 绘制收盘价图表
        import matplotlib.pyplot as plt
        plt.figure(figsize=(14, 7))
        plt.plot(df.index, df['close'], label='收盘价')
        plt.title('平安银行 2023 年收盘价走势')
        plt.xlabel('日期')
        plt.ylabel('价格 (元)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig("stock_price_2023.png")
        print("\n图表已保存为 stock_price_2023.png")
    else:
        print("❌ 数据获取失败")
