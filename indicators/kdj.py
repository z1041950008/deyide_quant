"""
kdj.py - KDJ 指标 (随机指标)

KDJ 又称随机指标，用于判断超买超卖
"""
import numpy as np
import pandas as pd
from typing import Tuple


def calculate_rsv(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 9
) -> pd.Series:
    """
    计算 RSV (未成熟随机值)
    
    公式: RSV = (收盘价 - N 日最低价) / (N 日最高价 - N 日最低价) × 100
    
    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        window: 周期数，默认 9
    
    返回:
        RSV 序列
    """
    lowest_low = low.rolling(window=window).min()
    highest_high = high.rolling(window=window).max()
    
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    return rsv


def calculate_kdj(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算 KDJ 指标
    
    公式:
    RSV = (CLOSE - LOWn) / (HIGHn - LOWn) × 100
    K = RSV × 1/m2 + K_prev × (1-1/m2)
    D = K × 1/m1 + D_prev × (1-1/m1)
    J = 3 × K - 2 × D
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
        n: RSV 周期，默认 9
        m1: K 的平滑周期，默认 3
        m2: D 的平滑周期，默认 3
    
    返回:
        (K, D, J) 三元组
    """
    # 计算 RSV
    rsv = calculate_rsv(high, low, close, n)
    
    # 计算 K 值 (RSV 的 M2 日移动平均)
    k = rsv.ewm(com=m2-1, adjust=False).mean()
    
    # 计算 D 值 (K 的 M1 日移动平均)
    d = k.ewm(com=m1-1, adjust=False).mean()
    
    # 计算 J 值
    j = 3 * k - 2 * d
    
    return k, d, j


def detect_overbought(k: pd.Series, d: pd.Series, threshold: float = 80) -> pd.Series:
    """
    检测超买信号
    
    参数:
        k: K 值
        d: D 值
        threshold: 超买阈值，默认 80
    
    返回:
        超买信号序列
    """
    overbought = (k > threshold) & (d > threshold)
    return overbought.astype(int)


def detect_oversold(k: pd.Series, d: pd.Series, threshold: float = 20) -> pd.Series:
    """
    检测超卖信号
    
    参数:
        k: K 值
        d: D 值
        threshold: 超卖阈值，默认 20
    
    返回:
        超卖信号序列
    """
    oversold = (k < threshold) & (d < threshold)
    return oversold.astype(int)


def detect_kdj_golden_cross(k: pd.Series, d: pd.Series) -> pd.Series:
    """
    检测 KDJ 金叉 (K 上穿 D)
    
    参数:
        k: K 值
        d: D 值
    
    返回:
        金叉信号序列
    """
    golden = (k > d) & (k.shift(1) <= d.shift(1))
    return golden.astype(int)


def detect_kdj_death_cross(k: pd.Series, d: pd.Series) -> pd.Series:
    """
    检测 KDJ 死叉 (K 下穿 D)
    
    参数:
        k: K 值
        d: D 值
    
    返回:
        死叉信号序列
    """
    death = (k < d) & (k.shift(1) >= d.shift(1))
    return death.astype(int)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    
    base = np.random.uniform(10, 20, 100).cumsum() / 10
    high = pd.Series(base + np.random.uniform(0, 1, 100), index=dates)
    low = pd.Series(base - np.random.uniform(0, 1, 100), index=dates)
    close = pd.Series(base + np.random.uniform(-0.5, 0.5, 100), index=dates)
    
    print("=" * 60)
    print("KDJ 指标示例")
    print("=" * 60)
    
    # 计算 KDJ
    k, d, j = calculate_kdj(high, low, close)
    
    print("\n【KDJ 前 15 个值】")
    result = pd.DataFrame({
        'close': close,
        'K': k.round(2),
        'D': d.round(2),
        'J': j.round(2)
    })
    print(result.head(15))
    
    # 检测信号
    overbought = detect_overbought(k, d)
    oversold = detect_oversold(k, d)
    golden = detect_kdj_golden_cross(k, d)
    death = detect_kdj_death_cross(k, d)
    
    print(f"\n【超买信号数量】: {overbought.sum()}")
    print(f"【超卖信号数量】: {oversold.sum()}")
    print(f"【金叉信号数量】: {golden.sum()}")
    print(f"【死叉信号数量】: {death.sum()}")
    
    print("\n✅ KDJ 指标计算完成！")
