"""
rsi.py - RSI 相对强弱指标 (Relative Strength Index)

用于判断超买超卖状态
"""
import numpy as np
import pandas as pd
from typing import Tuple


def calculate_rsi(
    close: pd.Series,
    window: int = 14
) -> pd.Series:
    """
    计算 RSI 指标
    
    公式:
    上涨幅度 = max(0, close_today - close_yesterday)
    下跌幅度 = max(0, close_yesterday - close_today)
    平均上涨 = MA(上涨幅度，N)
    平均下跌 = MA(下跌幅度，N)
    RS = 平均上涨 / 平均下跌
    RSI = 100 - 100 / (1 + RS)
    
    参数:
        close: 收盘价序列
        window: 周期数，默认 14
    
    返回:
        RSI 序列
    """
    # 计算价格变化
    delta = close.diff()
    
    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    # 计算平均上涨和平均下跌 (使用 EMA)
    avg_gain = gain.ewm(com=window-1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window-1, min_periods=window).mean()
    
    # 计算 RS 和 RSI
    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)
    
    # 处理除零情况
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    
    return rsi


def detect_overbought(rsi: pd.Series, threshold: float = 70) -> pd.Series:
    """
    检测超买信号
    
    参数:
        rsi: RSI 值
        threshold: 超买阈值，默认 70
    
    返回:
        超买信号序列
    """
    return (rsi > threshold).astype(int)


def detect_oversold(rsi: pd.Series, threshold: float = 30) -> pd.Series:
    """
    检测超卖信号
    
    参数:
        rsi: RSI 值
        threshold: 超卖阈值，默认 30
    
    返回:
        超卖信号序列
    """
    return (rsi < threshold).astype(int)


def detect_divergence(
    close: pd.Series,
    rsi: pd.Series,
    window: int = 20
) -> Tuple[pd.Series, pd.Series]:
    """
    检测 RSI 背离
    
    参数:
        close: 收盘价
        rsi: RSI 值
        window: 检测窗口
    
    返回:
        (底背离信号，顶背离信号)
    """
    bullish_div = pd.Series(0, index=close.index)
    bearish_div = pd.Series(0, index=close.index)
    
    for i in range(window, len(close)):
        # 底背离：价格创新低，RSI 未创新低
        if (close.iloc[i] < close.iloc[i-window:i].min() and
            rsi.iloc[i] > rsi.iloc[i-window:i].min()):
            bullish_div.iloc[i] = 1
        
        # 顶背离：价格创新高，RSI 未创新高
        if (close.iloc[i] > close.iloc[i-window:i].max() and
            rsi.iloc[i] < rsi.iloc[i-window:i].max()):
            bearish_div.iloc[i] = 1
    
    return bullish_div, bearish_div


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = pd.Series(np.random.uniform(10, 20, 100).cumsum() / 10, index=dates)
    
    print("=" * 60)
    print("RSI 指标示例")
    print("=" * 60)
    
    rsi = calculate_rsi(close, 14)
    
    print("\n【RSI 前 20 个值】")
    result = pd.DataFrame({
        'close': close.round(2),
        'RSI': rsi.round(2)
    })
    print(result.head(20))
    
    overbought = detect_overbought(rsi)
    oversold = detect_oversold(rsi)
    
    print(f"\n【超买信号数量】: {overbought.sum()}")
    print(f"【超卖信号数量】: {oversold.sum()}")
    
    print("\n✅ RSI 指标计算完成！")
