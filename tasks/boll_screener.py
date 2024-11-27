import pandas as pd
import numpy as np
from datetime import datetime
import akshare as ak
from typing import List, Dict

class StockScorer:
    def __init__(self):
        # 定义财务指标权重
        self.weights = {
            'ROE': 0.2,              # 净资产收益率
            'profit_growth': 0.15,    # 净利润增长率
            'gross_margin': 0.15,     # 毛利率
            'debt_ratio': -0.1,       # 资产负债率（负相关）
            'pe_ratio': -0.1,         # 市盈率（负相关）
            'pb_ratio': -0.1,         # 市净率（负相关）
            'revenue_growth': 0.1,    # 营收增长率
            'cash_ratio': 0.1         # 现金比率
        }
        
    def get_financial_data(self, stock_code: str) -> Dict:
        """获取股票财务指标"""
        try:
            # 获取主要财务指标
            financial = ak.stock_financial_abstract_ths(symbol=stock_code)
            if financial is None or financial.empty or len(financial) == 0:
                print(f"股票 {stock_code} 无财务数据")
                return None
            
            try:
                # 获取最新一期的财务数据
                latest = financial.iloc[0]
            except IndexError:
                print(f"股票 {stock_code} 无法获取最新财务数据")
                return None
            
            def safe_float(value, default=0.0):
                """安全地转换字符串到浮点数，处理空值和异常情况"""
                if pd.isna(value) or value == '' or value == '-':
                    return default
                try:
                    return float(value.strip('%')) if isinstance(value, str) else float(value)
                except (ValueError, AttributeError):
                    return default
            
            return {
                'ROE': safe_float(latest.get('净资产收益率')),
                'profit_growth': safe_float(latest.get('净利润同比增长率')),
                'gross_margin': safe_float(latest.get('销售毛利率')),
                'debt_ratio': safe_float(latest.get('资产负债率')),
                'cash_ratio': safe_float(latest.get('速动比率')),
                'revenue_growth': safe_float(latest.get('营业总收入同比增长率'))
            }
        except Exception as e:
            print(f"获取 {stock_code} 财务数据失败: {str(e)}")
            return None

    def normalize_score(self, data: Dict) -> float:
        """计算归一化后的得分"""
        score = 0
        # 定义各指标的参考范围
        metric_ranges = {
            'ROE': (0, 30),              # ROE 范围 0-30%
            'profit_growth': (-50, 100),  # 净利润增长率范围 -50% 到 100%
            'gross_margin': (0, 50),      # 毛利率范围 0-50%
            'debt_ratio': (0, 100),       # 资产负债率范围 0-100%
            'cash_ratio': (0, 3),         # 速动比率范围 0-3
            'revenue_growth': (-30, 100)  # 营收增长率范围 -30% 到 100%
        }
        
        for metric, weight in self.weights.items():
            if metric in data:
                value = data[metric]
                min_val, max_val = metric_ranges[metric]
                # 将数据限制在范围内
                value = max(min_val, min(value, max_val))
                # 归一化到0-1之间
                normalized_value = (value - min_val) / (max_val - min_val) if (max_val - min_val) != 0 else 0
                score += normalized_value * weight
                
        return max(0, min(score, 1))  # 确保最终分数在0-1之间

# 布林带选股策略
# 布林带是一个经典的趋势指标，通过计算股价的移动平均线和标准差，来确定股价的波动范围。
# 当股价从下轨上穿时，视为买入信号；当股价从上轨下穿时，视为卖出信号。
# 单纯使用布林带选股，效果不佳，需要结合其他指标进行综合分析。
# 经过测试，在A股市场，选择大市值股票，结合财务指标得分，效果较好。
class BollScreener:
    def __init__(self, period=20, std_dev=2, include_cyb=False, include_kcb=False, top_n=10):
        self.period = period
        self.std_dev = std_dev
        self.include_cyb = include_cyb
        self.include_kcb = include_kcb
        self.top_n = top_n  # 最终选取的股票数量
        self.scorer = StockScorer()
        
    def get_stock_list(self):
        """获取符合条件的股票列表"""
        print("正在获取股票列表...")
        
        # 获取所有A股基本信息
        stock_info = ak.stock_zh_a_spot_em()
        
        # 基础过滤：剔除ST和退市股票
        df = stock_info[~stock_info['名称'].str.contains('ST|退')]
        
        # 板块过滤
        if not self.include_cyb:
            df = df[~df['代码'].str.startswith('300')]
        if not self.include_kcb:
            df = df[~df['代码'].str.startswith('688')]
            
        # 获取流通市值数据并排序，选取最大的300只股票
        df['流通市值'] = df['流通市值'].astype(float)
        df = df.nlargest(300, '流通市值')
        
        return df[['代码', '名称', '最新价']].to_dict('records')

    def check_signals(self, data: pd.DataFrame) -> str:
        """检查布林带买卖信号"""
        # 计算布林带指标
        data['MA'] = data['收盘'].rolling(window=self.period).mean()
        data['STD'] = data['收盘'].rolling(window=self.period).std()
        data['Upper'] = data['MA'] + (self.std_dev * data['STD'])
        data['Lower'] = data['MA'] - (self.std_dev * data['STD'])
        
        # 获取最新数据
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 买入信号：价格从下轨上穿
        if latest['收盘'] > latest['Lower'] and prev['收盘'] <= prev['Lower']:
            return 'BUY'
        # 卖出信号：价格从上轨下穿
        elif latest['收盘'] < latest['Upper'] and prev['收盘'] >= prev['Upper']:
            return 'SELL'
        else:
            return 'HOLD'

    def run(self, trade_date: str = None) -> tuple:
        """
        运行布林带筛选策略
        Args:
            trade_date: 可选的交易日期，用于回测，格式为'YYYY-MM-DD'
        Returns:
            tuple: (买入信号列表, 卖出信号列表)
        """
        # 设置日期范围
        end_date = trade_date if trade_date else datetime.now().strftime("%Y-%m-%d")
        print(f"开始布林带选股 - {datetime.now()} (交易日期: {end_date})")
        
        # 获取初始股票池
        stock_list = self.get_stock_list()
        print(f"初始股票池数量: {len(stock_list)} (交易日期: {end_date})")
        
        # 获取前100个交易日的数据以确保有足够数据计算布林带
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - pd.Timedelta(days=150)).strftime("%Y%m%d")
        
        # 存储买卖信号的股票
        buy_signals = []
        sell_signals = []
        
        # 布林带筛选
        for i, stock in enumerate(stock_list, 1):
            try:
                # print(f"布林带筛选进度: {i}/{len(stock_list)} - {stock['代码']}")
                stock_data = ak.stock_zh_a_hist(
                    symbol=stock['代码'], 
                    period="daily",
                    start_date=start_date,
                    end_date=end_date.replace('-', ''),  # Convert YYYY-MM-DD to YYYYMMDD
                    adjust="qfq"  # 前复权
                )
                
                # 确保数据不为空且包含指定日期
                if stock_data.empty:
                    continue
                latest = stock_data.iloc[-1]
                signal = self.check_signals(stock_data)
                stock['latest_price'] = latest['收盘']
                if signal == 'BUY':
                    # 获取财务数据并计算得分
                    financial_data = self.scorer.get_financial_data(stock['代码'])
                    if financial_data:
                        score = self.scorer.normalize_score(financial_data)
                        buy_signals.append({
                            'code': stock['代码'],
                            'name': stock['名称'],
                            'score': score,
                            'financial_data': financial_data,
                            "close_price": latest['收盘']
                        })
                elif signal == 'SELL':
                    sell_signals.append({
                        'code': stock['代码'],
                        'name': stock['名称'],
                        "close_price": latest['收盘']
                    })
                    
            except Exception as e:
                print(f"处理股票 {stock['代码']} 时出错: {str(e)}")
                continue
        
        # 按得分排序买入信号
        buy_signals.sort(key=lambda x: x['score'], reverse=True)
        buy_signals = buy_signals[:self.top_n]  # 只保留得分最高的 top_n 只股票
        
        print(f"\n买入信号数量: {len(buy_signals)} (交易日期: {end_date})")
        print(f"卖出信号数量: {len(sell_signals)} (交易日期: {end_date})")
        
        return buy_signals, sell_signals, stock_list

if __name__ == "__main__":
    screener = BollScreener(include_cyb=False, include_kcb=False, top_n=10)
    buy_signals, sell_signals = screener.run() 