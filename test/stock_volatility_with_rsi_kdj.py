def is_volatile_stock(stock_data, rsi_period=14, kdj_period=9):
    """
    判断 股票的波动类型
    
    """
    import pandas as pd
    import numpy as np
    
    # 计算RSI
    delta = stock_data['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # 计算KDJ
    low_list = stock_data['最低'].rolling(window=kdj_period, min_periods=kdj_period).min()
    high_list = stock_data['最高'].rolling(window=kdj_period, min_periods=kdj_period).max()
    rsv = (stock_data['收盘'] - low_list) / (high_list - low_list) * 100
    k = pd.Series(rsv).ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    
    # 判断标准
    # 1. RSI波动频率：计算RSI穿越50线的次数
    rsi_crosses = np.sum(np.abs(np.diff(np.signbit(rsi - 50))))
    
    # 2. KDJ波动频率：计算J线穿越0的次数
    kdj_crosses = np.sum(np.abs(np.diff(np.signbit(j))))
    
    # 3. RSI波动幅度
    rsi_volatility = np.std(rsi)
    
    # 4. KDJ波动幅度
    kdj_volatility = np.std(j)
    
    # 设定阈值
    trading_days = len(stock_data)
    yearly_trading_days = 252
    years = trading_days / yearly_trading_days
    
    thresholds = {
        'volatile': {
            'rsi_crosses_per_year': 30,  # 频繁穿越，平均每两周穿越一次以上
            'kdj_crosses_per_year': 35,  # KDJ更敏感，穿越次数阈值更高
            'rsi_volatility': 20,        # RSI较大波动范围
            'kdj_volatility': 40         # KDJ波动范围更大
        },
        'non_volatile': {
            'rsi_crosses_per_year': 15,  # 平均每月穿越1-2次以下
            'kdj_crosses_per_year': 20,  # KDJ相对较少的穿越
            'rsi_volatility': 12,        # RSI保持在相对稳定范围
            'kdj_volatility': 25         # KDJ波动相对温和
        }
    }
    
    # 计算指标
    metrics = {
        'rsi_crosses_per_year': rsi_crosses/years,
        'kdj_crosses_per_year': kdj_crosses/years,
        'rsi_volatility': rsi_volatility,
        'kdj_volatility': kdj_volatility
    }
    
    # 判断是否为波动型
    is_volatile = (
        metrics['rsi_crosses_per_year'] >= thresholds['volatile']['rsi_crosses_per_year'] and
        metrics['kdj_crosses_per_year'] >= thresholds['volatile']['kdj_crosses_per_year'] and
        metrics['rsi_volatility'] >= thresholds['volatile']['rsi_volatility'] and
        metrics['kdj_volatility'] >= thresholds['volatile']['kdj_volatility']
    )
    
    # 判断是否为非波动型
    is_non_volatile = (
        metrics['rsi_crosses_per_year'] < thresholds['non_volatile']['rsi_crosses_per_year'] and
        metrics['kdj_crosses_per_year'] < thresholds['non_volatile']['kdj_crosses_per_year'] and
        metrics['rsi_volatility'] < thresholds['non_volatile']['rsi_volatility'] and
        metrics['kdj_volatility'] < thresholds['non_volatile']['kdj_volatility']
    )
    
    # 确定股票类型
    stock_type = '中等波动'  # 默认为中等波动
    if is_volatile:
        stock_type = '波动型'
    elif is_non_volatile:
        stock_type = '非波动型'
    
    analysis = {
        **metrics,
        'stock_type': stock_type
    }
    
    return stock_type, analysis


import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

def analyze_all_stocks():
  


    # 获取A股股票列表
    stock_list = ak.stock_zh_a_spot_em()
    # 过滤ST和退市股票
    stock_list = stock_list[~stock_list['名称'].str.contains('ST|退')]
    # 过滤科创板、创业板等
    stock_list = stock_list[~stock_list['代码'].str.startswith(('300', '301', '688', '8', '9', '4'))]
    # stock_list = stock_list.head(10)
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
    
    results = []
    total = len(stock_list)
    
    for idx, stock in stock_list.iterrows():
        try:
            print(f"处理进度: {idx+1}/{total} ({(idx+1)/total*100:.2f}%)")
            
            # 获取股票数据
            df = ak.stock_zh_a_hist(
                symbol=stock['代码'],
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if df is None or len(df) < 252:  # 至少需要一年的数据
                continue
                
            df = df.sort_values('日期')
            
            # 分别判断是否为波动型和非波动型
            stock_type, analysis = is_volatile_stock(df)
            
            result = {
                '股票代码': stock['代码'],
                '股票名称': stock['名称'],
                '最新价': stock['最新价'],
                '流通市值': stock['流通市值'],
                '股票类型': stock_type,
                'rsi穿越50线次数': analysis['rsi_crosses_per_year'],
                'kdj穿越0线次数': analysis['kdj_crosses_per_year'],
                'rsi标准差': analysis['rsi_volatility'],
                'kdj标准差': analysis['kdj_volatility']
            }
            results.append(result)
            
        except Exception as e:
            print(f"处理股票 {stock['代码']} 时出错: {str(e)}")
            continue
    
    results_df = pd.DataFrame(results)
    results_df.to_excel('stock_with_rsi_kdj.xlsx', index=False)
    
    # 统计各类型股票数量
    type_counts = results_df['股票类型'].value_counts()
    print("\n股票类型统计:")
    print(type_counts)
    
    return results_df

analyze_all_stocks()