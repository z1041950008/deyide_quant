"""
atr.py - ATR 波动率指标 (Average True Range)

用于衡量价格波动程度，常用于止损设置
"""
import numpy as np
import pandas as pd


def calculate_true_range(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series
) -> pd.Series:
    """
    计算真实波幅 (True Range)
    
    公式: TR = max(
        high - low,
        |high - close_prev|,
        |low - close_prev|
    )
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
    
    返回:
        TR 序列
    """
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14
) -> pd.Series:
    """
    计算 ATR (平均真实波幅)
    
    公式: ATR = MA(TR, N)
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
        window: 周期数，默认 14
    
    返回:
        ATR 序列
    """
    tr = calculate_true_range(high, low, close)
    atr = tr.ewm(span=window, adjust=False).mean()
    return atr


def calculate_atr_percent(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14
) -> pd.Series:
    """
    计算 ATR 百分比 (相对于收盘价)
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
        window: 周期数
    
    返回:
        ATR% 序列
    """
    atr = calculate_atr(high, low, close, window)
    atr_pct = atr / close * 100
    return atr_pct


def calculate_stop_loss(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    atr_window: int = 14,
    atr_multiplier: float = 2.0,
    position: str = 'long'
) -> pd.Series:
    """
    基于 ATR 计算止损位
    
    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        atr_window: ATR 周期
        atr_multiplier: ATR 倍数
        position: 'long' | 'short'
    
    返回:
        止损位序列
    """
    atr = calculate_atr(high, low, close, atr_window)
    
    if position == 'long':
        # 多头止损 = 收盘价 - ATR × 倍数
        stop_loss = close - atr * atr_multiplier
    else:
        # 空头止损 = 收盘价 + ATR × 倍数
        stop_loss = close + atr * atr_multiplier
    
    return stop_loss


def calculate_volatility_ratio(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    short_window: int = 7,
    long_window: int = 21
) -> pd.Series:
    """
    计算波动率比率 (短期 ATR / 长期 ATR)
    
    参数:
        high: 最高价
        low: 最低价
        close: 收盘价
        short_window: 短期窗口
        long_window: 长期窗口
    
    返回:
        波动率比率
    """
    tr = calculate_true_range(high, low, close)
    
    atr_short = tr.ewm(span=short_window, adjust=False).mean()
    atr_long = tr.ewm(span=long_window, adjust=False).mean()
    
    vr = atr_short / atr_long
    return vr


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    
    base = np.random.uniform(10, 20, 100).cumsum() / 10
    high = pd.Series(base + np.random.uniform(0, 1, 100), index=dates)
    low = pd.Series(base - np.random.uniform(0, 1, 100), index=dates)
    close = pd.Series(base + np.random.uniform(-0.5, 0.5, 100), index=dates)
    
    print("=" * 60)
    print("ATR 波动率指标示例")
    print("=" * 60)
    
    atr = calculate_atr(high, low, close)
    atr_pct = calculate_atr_percent(high, low, close)
    
    print("\n【ATR 前 20 个值】")
    result = pd.DataFrame({
        'close': close.round(2),
        'high': high.round(2),
        'low': low.round(2),
        'ATR': atr.round(3),
        'ATR%': atr_pct.round(2)
    })
    print(result.head(20))
    
    # 计算止损位
    stop_loss = calculate_stop_loss(close, high, low, position='long')
    print(f"\n【多头止损位示例】: {stop_loss.iloc[-1]:.2f}")
    
    vol_ratio = calculate_volatility_ratio(high, low, close)
    print(f"【波动率比率】: {vol_ratio.iloc[-1]:.2f}")
    
    print("\n✅ ATR 指标计算完成！")
