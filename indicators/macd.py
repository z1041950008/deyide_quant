"""
macd.py - MACD 指标 (Moving Average Convergence Divergence)

异同移动平均线，用于判断趋势强度和方向
"""
import numpy as np
import pandas as pd
from typing import Tuple
from .ma import calculate_ema


def calculate_macd(
    close: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算 MACD 指标
    
    公式:
    DIF = EMA(close, fast) - EMA(close, slow)
    DEA = EMA(DIF, signal)
    MACD 柱 = 2 × (DIF - DEA)
    
    参数:
        close: 收盘价序列
        fast_period: 快线周期，默认 12
        slow_period: 慢线周期，默认 26
        signal_period: 信号线周期，默认 9
    
    返回:
        (DIF, DEA, MACD 柱) 三元组
    """
    # 计算 DIF
    ema_fast = calculate_ema(close, fast_period)
    ema_slow = calculate_ema(close, slow_period)
    dif = ema_fast - ema_slow
    
    # 计算 DEA
    dea = calculate_ema(dif, signal_period)
    
    # 计算 MACD 柱
    macd_hist = 2 * (dif - dea)
    
    return dif, dea, macd_hist


def detect_macd_golden_cross(dif: pd.Series, dea: pd.Series) -> pd.Series:
    """
    检测 MACD 金叉 (DIF 上穿 DEA)
    
    参数:
        dif: DIF 线
        dea: DEA 线
    
    返回:
        金叉信号序列
    """
    golden = (dif > dea) & (dif.shift(1) <= dea.shift(1))
    return golden.astype(int)


def detect_macd_death_cross(dif: pd.Series, dea: pd.Series) -> pd.Series:
    """
    检测 MACD 死叉 (DIF 下穿 DEA)
    
    参数:
        dif: DIF 线
        dea: DEA 线
    
    返回:
        死叉信号序列
    """
    death = (dif < dea) & (dif.shift(1) >= dea.shift(1))
    return death.astype(int)


def detect_bullish_divergence(
    close: pd.Series,
    dif: pd.Series,
    window: int = 20
) -> pd.Series:
    """
    检测 MACD 底背离 (看涨背离)
    
    底背离：价格创新低，但 DIF 未创新低
    
    参数:
        close: 收盘价
        dif: DIF 线
        window: 检测窗口
    
    返回:
        底背离信号序列
    """
    signal = pd.Series(0, index=close.index)
    
    for i in range(window, len(close)):
        # 检查价格是否创新低
        price_window = close.iloc[i-window:i+1]
        current_price_low = price_window.min()
        
        # 检查 DIF 是否未创新低
        dif_window = dif.iloc[i-window:i+1]
        
        # 简化版背离检测
        if (close.iloc[i] < close.iloc[i-5] and 
            dif.iloc[i] > dif.iloc[i-5] and
            dif.iloc[i] > 0):
            signal.iloc[i] = 1
    
    return signal


def detect_bearish_divergence(
    close: pd.Series,
    dif: pd.Series,
    window: int = 20
) -> pd.Series:
    """
    检测 MACD 顶背离 (看跌背离)
    
    顶背离：价格创新高，但 DIF 未创新高
    
    参数:
        close: 收盘价
        dif: DIF 线
        window: 检测窗口
    
    返回:
        顶背离信号序列
    """
    signal = pd.Series(0, index=close.index)
    
    for i in range(window, len(close)):
        # 简化版背离检测
        if (close.iloc[i] > close.iloc[i-5] and 
            dif.iloc[i] < dif.iloc[i-5] and
            dif.iloc[i] < 0):
            signal.iloc[i] = 1
    
    return signal


def macd_trend(dif: pd.Series, lookback: int = 5) -> str:
    """
    判断 MACD 趋势
    
    参数:
        dif: DIF 线
        lookback: 回看周期
    
    返回:
        'bullish' | 'bearish' | 'neutral'
    """
    if len(dif) < lookback:
        return 'unknown'
    
    recent = dif.tail(lookback).dropna()
    if len(recent) < lookback:
        return 'unknown'
    
    # 判断 DIF 是否在零轴上方
    if recent.iloc[-1] > 0:
        # 判断是否向上
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
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = pd.Series(np.random.uniform(10, 20, 100).cumsum() / 10, index=dates)
    
    print("=" * 60)
    print("MACD 指标示例")
    print("=" * 60)
    
    # 计算 MACD
    dif, dea, macd_hist = calculate_macd(close)
    
    print("\n【MACD 前 10 个值】")
    result = pd.DataFrame({
        'close': close,
        'DIF': dif,
        'DEA': dea,
        'MACD': macd_hist
    })
    print(result.head(10))
    
    # 检测信号
    golden = detect_macd_golden_cross(dif, dea)
    death = detect_macd_death_cross(dif, dea)
    
    print(f"\n【金叉信号数量】: {golden.sum()}")
    print(f"【死叉信号数量】: {death.sum()}")
    
    # 判断趋势
    trend = macd_trend(dif)
    print(f"\n【MACD 趋势】: {trend}")
    
    print("\n✅ MACD 指标计算完成！")
