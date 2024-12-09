import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# https://github.com/z1041950008/deyide_quant
# 如果需要定制化开发，可以私信我
# 如果觉得不错，可以点个star，谢谢
# 后续会更新更多指标，敬请期待

def get_stock_data(stock_code, start_date, end_date):
    """获取股票在指定日期范围内的日线数据"""
    try:
        stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        stock_data['收盘'] = stock_data['收盘'].astype(float)
        return stock_data
    except Exception as e:
        print(f"获取股票数据时出错: {stock_code}, 错误信息: {e}")
        return None

def is_stable(stock_data, threshold=2):
    """判断股票是否在一个区间内波动"""
    # 计算收盘价的标准差
    std_dev = stock_data['收盘'].std()
    # 计算收盘价的平均值
    mean_price = stock_data['收盘'].mean()
    # 判断标准差是否小于阈值的比例
    return std_dev / mean_price < threshold

def filter_stocks(stock_codes, start_date, end_date, threshold=0.05):
    stable_stocks = []
    total = len(stock_codes)
    processed = 0

    def process_stock(code):
        nonlocal processed
        stock_data = get_stock_data(code, start_date, end_date)
        processed += 1
        print(f"处理进度: {processed}/{total} ({processed/total*100:.2f}%)")
        if stock_data is not None and is_stable(stock_data, threshold):
            return code
        return None

    with ThreadPoolExecutor() as executor:
        results = executor.map(process_stock, stock_codes)

    stable_stocks = [code for code in results if code is not None]
    return stable_stocks

def record_stock_metrics(stock_codes, start_date, end_date, threshold=0.05, output_file='stock_metrics.xlsx'):
    """记录所有股票的方差、平均值及其比值到Excel"""
    metrics = []
    total = len(stock_codes)
    stock_info = ak.stock_zh_a_spot_em()

    for i, code in enumerate(stock_codes, 1):
        print(f"处理进度: {i}/{total} ({i/total*100:.2f}%)")
        stock_data = get_stock_data(code, start_date, end_date)
        if stock_data is not None:
            std_dev = stock_data['收盘'].std()
            mean_price = stock_data['收盘'].mean()
            ratio = std_dev / mean_price
            
            # 获取股票的当前信息
            temp_stock_info = stock_info[stock_info['代码'] == code]
            if not temp_stock_info.empty:
                stock_name = temp_stock_info['名称'].values[0]
                current_price = temp_stock_info['最新价'].values[0]
                market_cap = temp_stock_info['流通市值'].values[0] 

                metrics.append({
                    '股票代码': code,
                    '股票名称': stock_name,
                    '当前价格': current_price,
                    '流通市值': market_cap,
                    '标准差': std_dev,
                    '平均价格': mean_price,
                    '波动值': ratio,
                    '波动阈值': threshold
                })

    # 将数据存储到Excel
    df = pd.DataFrame(metrics)
    df.to_excel(output_file, index=False)
    print(f"股票指标已保存到 {output_file}")

def main():
    # 获取A股股票列表
    stock_list = ak.stock_zh_a_spot_em()
    stock_list = stock_list[~stock_list['名称'].str.contains('ST|退')]
    # 板块过滤
    stock_list = stock_list[~stock_list['代码'].str.startswith('300')]
    stock_list = stock_list[~stock_list['代码'].str.startswith('301')]
    stock_list = stock_list[~stock_list['代码'].str.startswith('688')]
    stock_list = stock_list[~stock_list['代码'].str.startswith('8')]
    stock_list = stock_list[~stock_list['代码'].str.startswith('9')]
    stock_list = stock_list[~stock_list['代码'].str.startswith('4')]

    stock_codes = stock_list['代码'].tolist()
    # stock_codes = stock_codes[:200]

    # 设置日期范围为过去3年
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')

    # 筛选出在区间内波动的股票
    # stable_stocks = filter_stocks(stock_codes, start_date, end_date)
    # print(f"在过去3年内波动稳定的股票有: {stable_stocks}")

    # 记录所有股票的指标
    record_stock_metrics(stock_codes, start_date, end_date)

if __name__ == "__main__":
    main() 