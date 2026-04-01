"""
boll.py - 布林带指标 (Bollinger Bands)

由中轨、上轨、下轨组成，用于判断价格波动区间
"""
import numpy as np
import pandas as pd
from typing import Tuple


def calculate_boll(
    close: pd.Series,
    window: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    计算布林带指标
    
    公式:
    中轨 = SMA(close, N)
    上轨 = 中轨 + K × 标准差
    下轨 = 中轨 - K × 标准差
    带宽 = (上轨 - 下轨) / 中轨
    
    参数:
        close: 收盘价序列
        window: 周期数，默认 20
        num_std: 标准差倍数，默认 2
    
    返回:
        (中轨，上轨，下轨，带宽) 四元组
    """
    # 中轨 = 20 日均线
    middle = close.rolling(window=window).mean()
    
    # 标准差
    std = close.rolling(window=window).std()
    
    # 上下轨
    upper = middle + num_std * std
    lower = middle - num_std * std
    
    # 带宽
    bandwidth = (upper - lower) / middle * 100
    
    return middle, upper, lower, bandwidth


def detect_breakout(
    close: pd.Series,
    upper: pd.Series,
    lower: pd.Series
) -> Tuple[pd.Series, pd.Series]:
    """
    检测布林带突破信号
    
    参数:
        close: 收盘价
        upper: 上轨
        lower: 下轨
    
    返回:
        (上突破信号，下突破信号)
    """
    # 上突破：收盘价上穿上轨
    breakout_up = (close > upper) & (close.shift(1) <= upper.shift(1))
    
    # 下突破：收盘价下穿下轨
    breakout_down = (close < lower) & (close.shift(1) >= lower.shift(1))
    
    return breakout_up.astype(int), breakout_down.astype(int)


def detect_squeeze(
    upper: pd.Series,
    lower: pd.Series,
    middle: pd.Series,
    threshold: float = 5.0
) -> pd.Series:
    """
    检测布林带收口 (低波动率)
    
    参数:
        upper: 上轨
        lower: 下轨
        middle: 中轨
        threshold: 带宽阈值，默认 5%
    
    返回:
        收口信号序列
    """
    bandwidth = (upper - lower) / middle * 100
    squeeze = bandwidth < threshold
    return squeeze.astype(int)


def boll_position(close: pd.Series, upper: pd.Series, lower: pd.Series) -> pd.Series:
    """
    计算价格在布林带中的位置
    
    公式：%B = (close - lower) / (upper - lower)
    
    参数:
        close: 收盘价
        upper: 上轨
        lower: 下轨
    
    返回:
        %B 值序列 (0-1 之间)
    """
    return (close - lower) / (upper - lower)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = pd.Series(np.random.uniform(10, 20, 100).cumsum() / 10, index=dates)
    
    print("=" * 60)
    print("布林带指标示例")
    print("=" * 60)
    
    middle, upper, lower, bandwidth = calculate_boll(close)
    
    print("\n【布林带前 25 个值】")
    result = pd.DataFrame({
        'close': close.round(2),
        'upper': upper.round(2),
        'middle': middle.round(2),
        'lower': lower.round(2),
        'bandwidth': bandwidth.round(2)
    })
    print(result.head(25))
    
    breakout_up, breakout_down = detect_breakout(close, upper, lower)
    print(f"\n【上突破信号】: {breakout_up.sum()}")
    print(f"【下突破信号】: {breakout_down.sum()}")
    
    squeeze = detect_squeeze(upper, lower, middle)
    print(f"【收口信号】: {squeeze.sum()}")
    
    print("\n✅ 布林带指标计算完成！")
