"""
ma.py - 移动平均线指标 (Moving Average)

包含:
- SMA: 简单移动平均
- EMA: 指数移动平均
- WMA: 加权移动平均
"""
import numpy as np
import pandas as pd
from typing import Union


def calculate_sma(series: Union[pd.Series, np.ndarray], window: int) -> pd.Series:
    """
    计算简单移动平均线 (Simple Moving Average)
    
    公式: SMA = (P1 + P2 + ... + Pn) / n
    
    参数:
        series: 价格序列 (收盘价等)
        window: 周期数，如 5/10/20
    
    返回:
        SMA 值序列
    """
    series = pd.Series(series) if not isinstance(series, pd.Series) else series
    return series.rolling(window=window).mean()


def calculate_ema(series: Union[pd.Series, np.ndarray], window: int) -> pd.Series:
    """
    计算指数移动平均线 (Exponential Moving Average)
    
    公式:
    EMA_today = α × Price_today + (1-α) × EMA_yesterday
    α = 2 / (window + 1)
    
    参数:
        series: 价格序列
        window: 周期数
    
    返回:
        EMA 值序列
    """
    series = pd.Series(series) if not isinstance(series, pd.Series) else series
    return series.ewm(span=window, adjust=False).mean()


def calculate_wma(series: Union[pd.Series, np.ndarray], window: int) -> pd.Series:
    """
    计算加权移动平均线 (Weighted Moving Average)
    
    公式: WMA = (P1×1 + P2×2 + ... + Pn×n) / (1+2+...+n)
    越近的数据权重越大
    
    参数:
        series: 价格序列
        window: 周期数
    
    返回:
        WMA 值序列
    """
    series = pd.Series(series) if not isinstance(series, pd.Series) else series
    
    def wma_func(window_data):
        weights = np.arange(1, window + 1)
        return np.sum(window_data * weights) / np.sum(weights)
    
    return series.rolling(window=window).apply(wma_func, raw=True)


def detect_golden_cross(short_ma: pd.Series, long_ma: pd.Series) -> pd.Series:
    """
    检测金叉信号 (短期均线上穿长期均线)
    
    参数:
        short_ma: 短期均线
        long_ma: 长期均线
    
    返回:
        金叉信号序列 (1 表示金叉，0 表示无信号)
    """
    # 今天短期>长期，且昨天短期<=长期
    golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
    return golden_cross.astype(int)


def detect_death_cross(short_ma: pd.Series, long_ma: pd.Series) -> pd.Series:
    """
    检测死叉信号 (短期均线下穿长期均线)
    
    参数:
        short_ma: 短期均线
        long_ma: 长期均线
    
    返回:
        死叉信号序列 (1 表示死叉，0 表示无信号)
    """
    # 今天短期<长期，且昨天短期>=长期
    death_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
    return death_cross.astype(int)


def ma_trend(ma_series: pd.Series, lookback: int = 5) -> str:
    """
    判断均线趋势
    
    参数:
        ma_series: 均线序列
        lookback: 回看周期
    
    返回:
        'uptrend' | 'downtrend' | 'sideways'
    """
    if len(ma_series) < lookback:
        return 'unknown'
    
    recent = ma_series.tail(lookback).dropna()
    if len(recent) < lookback:
        return 'unknown'
    
    # 计算斜率
    slope = (recent.iloc[-1] - recent.iloc[0]) / lookback
    
    if slope > recent.iloc[0] * 0.01:  # 上涨超过 1%
        return 'uptrend'
    elif slope < -recent.iloc[0] * 0.01:  # 下跌超过 1%
        return 'downtrend'
    else:
        return 'sideways'


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = pd.Series(np.random.uniform(10, 20, 100).cumsum() / 10, index=dates)
    
    print("=" * 60)
    print("移动平均线指标示例")
    print("=" * 60)
    
    # 计算各种 MA
    sma5 = calculate_sma(close, 5)
    sma20 = calculate_sma(close, 20)
    ema12 = calculate_ema(close, 12)
    ema26 = calculate_ema(close, 26)
    
    print("\n【SMA5 前 10 个值】")
    print(sma5.head(10))
    
    print("\n【EMA12 前 10 个值】")
    print(ema12.head(10))
    
    # 检测金叉死叉
    golden = detect_golden_cross(sma5, sma20)
    death = detect_death_cross(sma5, sma20)
    
    print(f"\n【金叉信号数量】: {golden.sum()}")
    print(f"【死叉信号数量】: {death.sum()}")
    
    # 判断趋势
    trend = ma_trend(sma20)
    print(f"\n【SMA20 趋势】: {trend}")
    
    print("\n✅ MA 指标计算完成！")
