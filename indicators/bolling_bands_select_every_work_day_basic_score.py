import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import akshare as ak

# https://github.com/z1041950008/deyide_quant
# 获取股票板块类型
# 如果需要定制化开发，可以私信我
# 如果觉得不错，可以点个star，谢谢
# 后续会更新更多指标，敬请期待

def get_board_type(stock_code):
    stock_code = str(stock_code).strip()  # 确保股票代码是字符串类型并去除空格

    # 判断科创板：股票代码以 '688' 开头
    if stock_code.startswith('688'):
        return '科创板'
    # 判断创业板：股票代码以 '300' 开头
    elif stock_code.startswith('300'):
        return '创业板'
    # 判断上海主板：股票代码以 '600' 或 '601' 开头
    elif stock_code.startswith('600') or stock_code.startswith('601') or stock_code.startswith('602') or stock_code.startswith('603') or stock_code.startswith('605'):
        return '上海主板'
    # 判断深圳主板：股票代码以 '000' 或 '002' 开头
    elif stock_code.startswith('000') or stock_code.startswith('002'):
        return '深圳主板'
    # 假设北京市场：股票代码以 '800' 开头
    elif stock_code.startswith('800'):
        return '北京市场'
    else:
        return '未知'
# 定义布林带计算函数
def calculate_bollinger_bands(df, window=20, num_std=2):
    """
    计算布林带
    :param df: 股票历史数据（DataFrame）
    :param window: 计算移动平均的窗口期，默认20日
    :param num_std: 计算标准差的倍数，默认2倍
    :return: 包含布林带计算结果的DataFrame
    """
    df['SMA'] = df['收盘'].rolling(window=window).mean()  # 计算简单移动平均线（中轨）
    df['std'] = df['收盘'].rolling(window=window).std()  # 计算标准差
    df['upper'] = df['SMA'] + num_std * df['std']  # 上轨
    df['lower'] = df['SMA'] - num_std * df['std']  # 下轨
    return df

stock_df = ak.stock_zh_a_spot_em()
stock_df['代码'] = stock_df['代码'].astype(str)

stock_df = stock_df[['代码', '名称', '市盈率-动态', '市净率', '流通市值']]
stock_df['板块'] = stock_df['代码'].apply(get_board_type)

stock_df = stock_df.sort_values(by='流通市值', ascending=False)
stock_df['布林带买入'] = None 
stock_df['布林带卖出'] = None
stock_df = stock_df.head(300)
# print(stock_df)

def score_stock(stock_df):
    for index, row in stock_df.iterrows():
        print("processed ", index, "rows")

        stock_code = row['代码']

        stock_financial_analysis_indicator_df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按报告期")
        # print(stock_financial_analysis_indicator_df.iloc[0])
        if len(stock_financial_analysis_indicator_df) > 0:
            if '净资产收益率' in stock_financial_analysis_indicator_df.columns and isinstance(stock_financial_analysis_indicator_df.iloc[0]['净资产收益率'], str):
                stock_df.at[index, '净资产收益率'] = stock_financial_analysis_indicator_df.iloc[0]['净资产收益率'].replace("%", "")
            if '资产负债率' in stock_financial_analysis_indicator_df.columns and isinstance(stock_financial_analysis_indicator_df.iloc[0]['资产负债率'], str):
                stock_df.at[index,'资产负债率'] = stock_financial_analysis_indicator_df.iloc[0]['资产负债率'].replace("%", "")
            if '销售毛利率' in stock_financial_analysis_indicator_df.columns and isinstance(stock_financial_analysis_indicator_df.iloc[0]['销售毛利率'], str):
                stock_df.at[index,'销售毛利率'] = stock_financial_analysis_indicator_df.iloc[0]['销售毛利率'].replace("%", "")
            

    scaler = MinMaxScaler()

    # 标准化所有指标列（不包括股票代码）
    columns_to_normalize = ['市盈率-动态', '市净率', '流通市值', '净资产收益率', '资产负债率', '销售毛利率']
    stock_df[columns_to_normalize] = scaler.fit_transform(stock_df[columns_to_normalize])

    # 对市盈率、市净率、资产负债率进行反转处理（越低越好）
    stock_df['市盈率-动态'] = 1 - stock_df['市盈率-动态']  # 越低越好，反转标准化值
    stock_df['市净率'] = 1 - stock_df['市净率']            # 越低越好，反转标准化值
    stock_df['资产负债率'] = 1 - stock_df['资产负债率']    # 越低越好，反转标准化值


    # 定义权重
    weights = {
        '市盈率-动态': 0.2,
        '市净率': 0.15,
        '流通市值': 0.1,
        '净资产收益率': 0.25,
        '资产负债率': 0.15,
        '销售毛利率': 0.15
    }

    # 计算综合得分
    stock_df['综合得分'] = (
        stock_df['市盈率-动态'].fillna(0) * weights['市盈率-动态'] +
        stock_df['市净率'].fillna(0) * weights['市净率'] +
        stock_df['流通市值'].fillna(0) * weights['流通市值'] +
        stock_df['净资产收益率'].fillna(0) * weights['净资产收益率'] +
        stock_df['资产负债率'].fillna(0) * weights['资产负债率'] +
        stock_df['销售毛利率'].fillna(0) * weights['销售毛利率']
    )

    # 排序，得分高的股票排名靠前
    stock_df = stock_df.sort_values(by='综合得分', ascending=False)

    # 显示最终排序的结果
    # print(df_sorted[['代码', '综合得分']])
    return stock_df

stock_df = score_stock(stock_df)

from datetime import datetime
from dateutil.relativedelta import relativedelta

# 获取今天的日期
today = datetime.today()
# 获取两个月前的日期
two_months_ago = today - relativedelta(months=2)

e_date = today.strftime('%Y%m%d')
s_date = two_months_ago.strftime('%Y%m%d')

for stock_code in stock_df['代码']:
    if stock_code == '002714':
        pass
    try:
        # 获取股票的历史数据（收盘价）
        stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=s_date, end_date=e_date, adjust="qfq")

        # 如果历史数据少于20天，跳过
        if len(stock_data) < 20:
            continue

        # 计算布林带
        stock_data = calculate_bollinger_bands(stock_data)

        # 获取最新数据的收盘价、下轨和上轨
        latest_data = stock_data.iloc[-1]
        latest_close = latest_data['收盘']
        lower_band = latest_data['lower']
        upper_band = latest_data['upper']

        # 获取前一天的收盘价和布林带数据
        previous_data = stock_data.iloc[-2]
        previous_close = previous_data['收盘']
        previous_lower_band = previous_data['lower']
        previous_upper_band = previous_data['upper']

        # 判断当天的收盘价是否符合布林带买入条件
        if previous_close < previous_lower_band and latest_close > lower_band:
            stock_df.loc[stock_df['代码'] == stock_code, '布林带买入'] = 1
        # 判断当天的收盘价是否符合布林带买入条件
        if previous_close < previous_upper_band and latest_close > upper_band:
            stock_df.loc[stock_df['代码'] == stock_code, '布林带卖出'] = 1

    except Exception as e:
        print(f"获取股票 {stock_code} 数据时发生错误: {e}")
        continue

# print(stock_df)
stock_df.to_excel("excel_stock/bolling_bands_select_every_work_day_basic_score.xlsx")
