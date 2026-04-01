"""
cci.py - CCI 顺势指标 (Commodity Channel Index)

用于判断价格是否偏离统计平均值
"""
import numpy as np
import pandas as pd


def calculate_typical_price(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series
) -> pd.Series:
    """
    计算典型价格
    
    公式: TP = (high + low + close) / 3
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
    
    返回:
        典型价格序列
    """
    return (high + low + close) / 3


def calculate_cci(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20
) -> pd.Series:
    """
    计算 CCI 指标
    
    公式:
    TP = (high + low + close) / 3
    MA = SMA(TP, N)
    MD = MA(|TP - MA|, N)
    CCI = (TP - MA) / (0.015 × MD)
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
        window: 周期数，默认 20
    
    返回:
        CCI 序列
    """
    # 计算典型价格
    tp = calculate_typical_price(high, low, close)
    
    # 计算移动平均
    ma = tp.rolling(window=window).mean()
    
    # 计算平均偏差
    deviation = (tp - ma).abs()
    md = deviation.rolling(window=window).mean()
    
    # 计算 CCI
    cci = (tp - ma) / (0.015 * md)
    
    return cci


def detect_overbought(cci: pd.Series, threshold: float = 100) -> pd.Series:
    """
    检测超买信号
    
    参数:
        cci: CCI 值
        threshold: 超买阈值，默认 100
    
    返回:
        超买信号序列
    """
    return (cci > threshold).astype(int)


def detect_oversold(cci: pd.Series, threshold: float = -100) -> pd.Series:
    """
    检测超卖信号
    
    参数:
        cci: CCI 值
        threshold: 超卖阈值，默认 -100
    
    返回:
        超卖信号序列
    """
    return (cci < threshold).astype(int)


def detect_trend_change(cci: pd.Series) -> pd.Series:
    """
    检测趋势变化 (CCI 穿越零轴)
    
    参数:
        cci: CCI 值
    
    返回:
        趋势变化信号 (1=上穿零轴，-1=下穿零轴)
    """
    signal = pd.Series(0, index=cci.index)
    
    # 上穿零轴
    signal[(cci > 0) & (cci.shift(1) <= 0)] = 1
    
    # 下穿零轴
    signal[(cci < 0) & (cci.shift(1) >= 0)] = -1
    
    return signal


def cci_trend(cci: pd.Series, lookback: int = 5) -> str:
    """
    判断 CCI 趋势
    
    参数:
        cci: CCI 值
        lookback: 回看周期
    
    返回:
        'bullish' | 'bearish' | 'neutral'
    """
    if len(cci) < lookback:
        return 'unknown'
    
    recent = cci.tail(lookback).dropna()
    if len(recent) < lookback:
        return 'unknown'
    
    # 判断是否在零轴上方
    if recent.iloc[-1] > 0:
        if recent.iloc[-1] > recent.iloc[0]:
            return 'bullish'
        else:
            return 'neutral'
    else:
        if recent.iloc[-1] < recent.iloc[0]:
            return 'bearish'
        else:
            return 'neutral'


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    
    base = np.random.uniform(10, 20, 100).cumsum() / 10
    high = pd.Series(base + np.random.uniform(0, 1, 100), index=dates)
    low = pd.Series(base - np.random.uniform(0, 1, 100), index=dates)
    close = pd.Series(base + np.random.uniform(-0.5, 0.5, 100), index=dates)
    
    print("=" * 60)
    print("CCI 顺势指标示例")
    print("=" * 60)
    
    cci = calculate_cci(high, low, close)
    
    print("\n【CCI 前 25 个值】")
    result = pd.DataFrame({
        'close': close.round(2),
        'CCI': cci.round(2)
    })
    print(result.head(25))
    
    overbought = detect_overbought(cci)
    oversold = detect_oversold(cci)
    trend_change = detect_trend_change(cci)
    
    print(f"\n【超买信号】: {overbought.sum()}")
    print(f"【超卖信号】: {oversold.sum()}")
    print(f"【上穿零轴】: {(trend_change == 1).sum()}")
    print(f"【下穿零轴】: {(trend_change == -1).sum()}")
    
    trend = cci_trend(cci)
    print(f"\n【CCI 趋势】: {trend}")
    
    print("\n✅ CCI 指标计算完成！")
