import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
from typing import List, Dict

# https://github.com/z1041950008/deyide_quant
# 如果需要定制化开发，可以私信我
# 如果觉得不错，可以点个star，谢谢
# 后续会更新更多指标，敬请期待

class JTMomentumScreener:
    def __init__(self, 
                 formation_period=6,    # 形成期（月）
                 holding_period=3,      # 持有期（月）
                 include_cyb=False, 
                 include_kcb=False, 
                 top_n=10):
        self.formation_period = formation_period
        self.holding_period = holding_period
        self.include_cyb = include_cyb
        self.include_kcb = include_kcb
        self.top_n = top_n
        
    def get_stock_list(self):
        print("正在获取股票列表...")
        
        stock_info = ak.stock_zh_a_spot_em()
        
        df = stock_info[~stock_info['名称'].str.contains('ST|退')]
        if not self.include_cyb:
            df = df[~df['代码'].str.startswith('300')]
        if not self.include_kcb:
            df = df[~df['代码'].str.startswith('688')]
            
        # 获取流通市值数据并排序，选取最大的300只股票
        df['流通市值'] = df['流通市值'].astype(float)
        df = df.nlargest(300, '流通市值')
        
        return df[['代码', '名称', '最新价']].to_dict('records')
    """计算动量分数"""
    def calculate_momentum(self, data: pd.DataFrame) -> float:

        try:
            # 计算收益率
            returns = (data['收盘'] - data['收盘'].shift(1)) / data['收盘'].shift(1)
            
            # 计算过去formation_period月的累积收益
            cumulative_return = (1 + returns).prod() - 1
            
            # 计算波动率调整后的动量得分
            volatility = returns.std()
            momentum_score = cumulative_return / volatility if volatility != 0 else 0
            
            return momentum_score
        except Exception as e:
            print(f"计算动量分数时出错: {str(e)}")
            return 0

    def run(self, trade_date: str = None) -> tuple:
        end_date = trade_date if trade_date else datetime.now().strftime("%Y-%m-%d")
        print(f"开始JT动量选股 - {datetime.now()} (交易日期: {end_date})")
        
        # 获取初始股票池
        stock_list = self.get_stock_list()
        print(f"初始股票池数量: {len(stock_list)}")
        
        # 计算回看期起始日期（形成期）
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - 
                     timedelta(days=self.formation_period * 30 + 30)).strftime("%Y%m%d")
        
        momentum_signals = []
        
        # 动量策略筛选
        for i, stock in enumerate(stock_list, 1):
            try:
                stock_data = ak.stock_zh_a_hist(
                    symbol=stock['代码'],
                    period="daily",
                    start_date=start_date,
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"
                )
                
                if stock_data.empty:
                    continue
                    
                # 计算动量得分
                momentum_score = self.calculate_momentum(stock_data)
                    
                momentum_signals.append({
                    'code': stock['代码'],
                    'name': stock['名称'],
                    'momentum_score': momentum_score,
                    'close_price': stock_data.iloc[-1]['收盘']
                })
                    
            except Exception as e:
                print(f"处理股票 {stock['代码']} 时出错: {str(e)}")
                continue
        
        momentum_signals.sort(key=lambda x: x['momentum_score'], reverse=True)
        
        # 选取得分最高的top_n只股票作为买入信号
        buy_signals = momentum_signals[:self.top_n]
        
        # 选取得分最低的top_n只股票作为卖出信号
        sell_signals = momentum_signals[-self.top_n:]
        
        print(f"\n买入信号数量: {len(buy_signals)} (交易日期: {end_date})")
        print(f"卖出信号数量: {len(sell_signals)} (交易日期: {end_date})")
        
        return buy_signals, sell_signals, stock_list

if __name__ == "__main__":
    screener = JTMomentumScreener(
        formation_period=6,    # 6个月形成期
        holding_period=3,      # 3个月持有期
        include_cyb=False, 
        include_kcb=False, 
        top_n=10
    )
    buy_signals, sell_signals, _ = screener.run() 