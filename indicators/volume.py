"""
volume.py - 成交量指标

包含成交量均线、量比等指标
"""
import numpy as np
import pandas as pd
from .ma import calculate_sma


def calculate_volume_ma(volume: pd.Series, window: int = 5) -> pd.Series:
    """
    计算成交量均线
    
    参数:
        volume: 成交量序列
        window: 周期数
    
    返回:
        成交量均线
    """
    return calculate_sma(volume, window)


def calculate_volume_ratio(
    volume: pd.Series,
    window: int = 5
) -> pd.Series:
    """
    计算量比
    
    公式：量比 = 当日成交量 / 过去 N 日平均成交量
    
    参数:
        volume: 成交量序列
        window: 周期数
    
    返回:
        量比序列
    """
    volume_ma = calculate_volume_ma(volume, window)
    volume_ratio = volume / volume_ma
    return volume_ratio


def detect_volume_spike(
    volume: pd.Series,
    window: int = 20,
    threshold: float = 2.0
) -> pd.Series:
    """
    检测成交量异常放大
    
    参数:
        volume: 成交量
        window: 参考周期
        threshold: 放大倍数阈值
    
    返回:
        放量信号序列
    """
    volume_ma = calculate_volume_ma(volume, window)
    spike = volume > volume_ma * threshold
    return spike.astype(int)


def detect_volume_shrink(
    volume: pd.Series,
    window: int = 20,
    threshold: float = 0.5
) -> pd.Series:
    """
    检测成交量萎缩
    
    参数:
        volume: 成交量
        window: 参考周期
        threshold: 萎缩阈值
    
    返回:
        缩量信号序列
    """
    volume_ma = calculate_volume_ma(volume, window)
    shrink = volume < volume_ma * threshold
    return shrink.astype(int)


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算 OBV 能量潮
    
    公式:
    如果今日收盘 > 昨日收盘：OBV = 昨日 OBV + 今日成交量
    如果今日收盘 < 昨日收盘：OBV = 昨日 OBV - 今日成交量
    如果今日收盘 = 昨日收盘：OBV = 昨日 OBV
    
    参数:
        close: 收盘价
        volume: 成交量
    
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


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = pd.Series(np.random.uniform(10, 20, 100).cumsum() / 10, index=dates)
    volume = pd.Series(np.random.randint(1000, 10000, 100), index=dates)
    
    print("=" * 60)
    print("成交量指标示例")
    print("=" * 60)
    
    vol_ma = calculate_volume_ma(volume, 5)
    vol_ratio = calculate_volume_ratio(volume, 5)
    
    print("\n【成交量均线前 10 个值】")
    result = pd.DataFrame({
        'volume': volume,
        'vol_ma5': vol_ma.round(0),
        'vol_ratio': vol_ratio.round(2)
    })
    print(result.head(10))
    
    spike = detect_volume_spike(volume)
    shrink = detect_volume_shrink(volume)
    print(f"\n【放量信号】: {spike.sum()}")
    print(f"【缩量信号】: {shrink.sum()}")
    
    obv = calculate_obv(close, volume)
    print(f"\n【OBV 最终值】: {obv.iloc[-1]:.0f}")
    
    print("\n✅ 成交量指标计算完成！")
