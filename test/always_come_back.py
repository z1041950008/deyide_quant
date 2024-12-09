import akshare as ak
import pandas as pd
import talib
import numpy as np
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
# https://github.com/z1041950008/deyide_quant
# 如果需要定制化开发，可以私信我
# 如果觉得不错，可以点个star，谢谢
# 后续会更新更多指标，敬请期待
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
stock_list = stock_list[~stock_list['代码'].str.contains('ST')]

stock_codes = stock_list['代码'].tolist() # 示例：前50只股票

def get_technical_indicators(stock_data):
    """获取技术面参数"""
    stock_data['布林上轨'], stock_data['布林中轨'], stock_data['布林下轨'] = talib.BBANDS(stock_data['收盘'], timeperiod=20)
    stock_data['ATR'] = talib.ATR(stock_data['最高'], stock_data['最低'], stock_data['收盘'], timeperiod=14)
    stock_data['ATR_Ratio'] = stock_data['ATR'] / stock_data['收盘']
    stock_data['均线'] = stock_data['收盘'].rolling(60).mean()
    stock_data['偏离率'] = (stock_data['收盘'] - stock_data['均线']).abs() / stock_data['均线']
    return stock_data

def get_fundamental_data(stock_code):
    """获取基本面参数"""
    try:
        financial_data = ak.stock_financial_abstract_ths(symbol=stock_code).iloc[0]

        # 如果值为空或无效，设置为0
        roe = float(financial_data['净资产收益率'].replace('%', '') ) if financial_data['净资产收益率'] else 0
        eps = float(financial_data['基本每股收益']) if financial_data['基本每股收益'] else 0
        debt_ratio = float(financial_data['资产负债率'].replace('%', '')) if financial_data['资产负债率'] else 0
        revenue_growth = float(financial_data['营业总收入同比增长率'].replace('%', '')) if financial_data['营业总收入同比增长率'] else 0
    except Exception as e:
        print(f"处理财务数据时出错: {e}")
        return 0, 0, 0, 0
    return roe, eps, debt_ratio, revenue_growth

def check_company_announcements(stock_code):
    """检查公司公告是否有重大消息"""
    announcements = ak.stock_notice_report(symbol=stock_code)
    return not any("重大" in row['公告标题'] for _, row in announcements.iterrows())

def process_stock(code):
    try:
        # 获取股票日线数据
        stock_data = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        stock_data['收盘'] = stock_data['收盘'].astype(float)
        stock_data['布林下轨'] = stock_data['布林下轨'].astype(float)

        lastes_cp_gt_boll_down = stock_data['收盘'].iloc[-1] > stock_data['布林下轨'].iloc[-1]
        pre_cp_lt_boll_down = stock_data['收盘'].iloc[-2] < stock_data['布林下轨'].iloc[-2]
        # 计算技术面参数
        stock_data = get_technical_indicators(stock_data)
        atr_ratio = stock_data['ATR_Ratio'].iloc[-1]
        deviation_rate = stock_data['偏离率'].mean()

        # 获取基本面参数
        roe, eps, debt_ratio, revenue_growth = get_fundamental_data(code)

        # 筛选条件
        if (
            lastes_cp_gt_boll_down and 
            pre_cp_lt_boll_down and
            atr_ratio < 0.02 and
            deviation_rate < 0.05 and
            roe >= 10 and
            eps > 0 and
            debt_ratio <= 50 and
            revenue_growth >= 10 and
            check_company_announcements(code)
        ):
            return {
                "股票代码": code,
                "ATR比例": atr_ratio,
                "均线偏离率": deviation_rate,
                "ROE": roe,
                "EPS": eps,
                "资产负债率": debt_ratio,
                "营收增长率": revenue_growth
            }
    except Exception as e:
        print(f"处理股票 {code} 时出错: {e}")
        traceback.print_exc()
    return None

def filter_stocks(stock_codes):
    results = []
    total = len(stock_codes)
    completed = 0
    
    print(f"开始处理共 {total} 只股票...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_stock, code): code for code in stock_codes}
        for future in as_completed(futures):
            completed += 1
            code = futures[future]
            print(f"进度: {completed}/{total} ({(completed/total*100):.1f}%) - 处理股票: {code}")
            
            result = future.result()
            if result:
                results.append(result)
                print(f"股票 {code} 符合筛选条件！")
    
    print(f"\n筛选完成！共找到 {len(results)} 只符合条件的股票")
    return pd.DataFrame(results)



def save_all_stock_indicators(stock_codes):
    """保存所有股票的技术面和基本面指标到Excel"""
    all_results = []
    total = len(stock_codes)
    completed = 0
    
    print(f"开始收集 {total} 只股票的详细指标...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_stock_all_indicators, code): code for code in stock_codes}
        for future in as_completed(futures):
            completed += 1
            code = futures[future]
            print(f"进度: {completed}/{total} ({(completed/total*100):.1f}%) - 处理股票: {code}")
            
            result = future.result()
            if result:
                all_results.append(result)
    
    print(f"\n数据收集完成！共收集了 {len(all_results)} 只股票的指标")
    all_stocks_df = pd.DataFrame(all_results)
    all_stocks_df.to_excel('all_stocks_indicators.xlsx', index=False)
    return all_stocks_df

def process_stock_all_indicators(code):
    """处理单个股票的所有指标，不做筛选"""
    try:
        # 获取股票日线数据
        stock_data = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        stock_data['收盘'] = stock_data['收盘'].astype(float)
        stock_data['最高'] = stock_data['最高'].astype(float)
        stock_data['最低'] = stock_data['最低'].astype(float)

        # 计算技术面参数
        stock_data = get_technical_indicators(stock_data)
        atr_ratio = stock_data['ATR_Ratio'].iloc[-1]
        deviation_rate = stock_data['偏离率'].mean()

        # 获取基本面参数
        roe, eps, debt_ratio, revenue_growth = get_fundamental_data(code)

        # 获取股票名称
        stock_name = stock_list[stock_list['代码'] == code]['名称'].iloc[0]

        return {
            "股票代码": code,
            "股票名称": stock_name,
            "ATR比例": atr_ratio,
            "均线偏离率": deviation_rate,
            "ROE": roe,
            "EPS": eps,
            "资产负债率": debt_ratio,
            "营收增长率": revenue_growth,
            "最新收盘价": stock_data['收盘'].iloc[-1],
            "20日布林上轨": stock_data['布林上轨'].iloc[-1],
            "20日布林中轨": stock_data['布林中轨'].iloc[-1],
            "20日布林下轨": stock_data['布林下轨'].iloc[-1],
            "60日均线": stock_data['均线'].iloc[-1]
        }
    except Exception as e:
        print(f"处理股票 {code} 时出错: {e}")
        traceback.print_exc()
    return None


# 运行筛选并保存结果到 Excel
# filtered_stocks_df = filter_stocks(stock_codes)
# output_path = 'alway_come_back.xlsx'
# filtered_stocks_df.to_excel(output_path, index=False)

# 记录所有股票的指标
# 可以看着数据来筛选
all_stocks_df = save_all_stock_indicators(stock_codes)

