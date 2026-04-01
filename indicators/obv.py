"""
obv.py - OBV 能量潮指标 (On-Balance Volume)

通过成交量变化预测价格趋势
"""
import numpy as np
import pandas as pd
from .ma import calculate_sma


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算 OBV 能量潮
    
    公式:
    如果 close_today > close_yesterday: OBV = OBV_prev + volume
    如果 close_today < close_yesterday: OBV = OBV_prev - volume
    如果 close_today = close_yesterday: OBV = OBV_prev
    
    参数:
        close: 收盘价序列
        volume: 成交量序列
    
    返回:
        OBV 序列
    """
    obv = pd.Series(0.0, index=close.index)
    
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv


def calculate_obv_ma(obv: pd.Series, window: int = 30) -> pd.Series:
    """
    计算 OBV 的移动平均线
    
    参数:
        obv: OBV 序列
        window: 周期数
    
    返回:
        OBV 均线
    """
    return calculate_sma(obv, window)


def detect_obv_trend(obv: pd.Series, window: int = 10) -> str:
    """
    判断 OBV 趋势
    
    参数:
        obv: OBV 序列
        window: 回看周期
    
    返回:
        'uptrend' | 'downtrend' | 'sideways'
    """
    if len(obv) < window:
        return 'unknown'
    
    recent = obv.tail(window).dropna()
    if len(recent) < window:
        return 'unknown'
    
    # 计算斜率
    slope = (recent.iloc[-1] - recent.iloc[0]) / window
    
    if slope > 0:
        return 'uptrend'
    elif slope < 0:
        return 'downtrend'
    else:
        return 'sideways'


def detect_divergence(
    close: pd.Series,
    obv: pd.Series,
    window: int = 20
) -> tuple:
    """
    检测 OBV 背离
    
    参数:
        close: 收盘价
        obv: OBV 值
        window: 检测窗口
    
    返回:
        (底背离，顶背离)
    """
    bullish_div = pd.Series(0, index=close.index)
    bearish_div = pd.Series(0, index=close.index)
    
    for i in range(window, len(close)):
        # 底背离：价格创新低，OBV 未创新低
        if (close.iloc[i] < close.iloc[i-window:i].min() and
            obv.iloc[i] > obv.iloc[i-window:i].min()):
            bullish_div.iloc[i] = 1
        
        # 顶背离：价格创新高，OBV 未创新高
        if (close.iloc[i] > close.iloc[i-window:i].max() and
            obv.iloc[i] < obv.iloc[i-window:i].max()):
            bearish_div.iloc[i] = 1
    
    return bullish_div, bearish_div


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = pd.Series(np.random.uniform(10, 20, 100).cumsum() / 10, index=dates)
    volume = pd.Series(np.random.randint(1000, 10000, 100), index=dates)
    
    print("=" * 60)
    print("OBV 能量潮指标示例")
    print("=" * 60)
    
    obv = calculate_obv(close, volume)
    obv_ma = calculate_obv_ma(obv, 30)
    
    print("\n【OBV 前 15 个值】")
    result = pd.DataFrame({
        'close': close.round(2),
        'volume': volume,
        'OBV': obv.round(0),
        'OBV_MA30': obv_ma.round(0)
    })
    print(result.head(15))
    
    trend = detect_obv_trend(obv)
    print(f"\n【OBV 趋势】: {trend}")
    
    print("\n✅ OBV 指标计算完成！")
