"""
test_indicators.py - 指标模块单元测试
"""
import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '..')

from indicators.ma import calculate_sma, calculate_ema
from indicators.macd import calculate_macd
from indicators.rsi import calculate_rsi


def test_sma():
    """测试 SMA 计算"""
    prices = pd.Series([1, 2, 3, 4, 5])
    sma = calculate_sma(prices, 3)
    
    assert len(sma) == 5
    assert sma.iloc[2] == 2.0
    assert sma.iloc[4] == 4.0
    print("✅ SMA 测试通过")


def test_ema():
    """测试 EMA 计算"""
    prices = pd.Series([1, 2, 3, 4, 5])
    ema = calculate_ema(prices, 3)
    
    assert len(ema) == 5
    assert not ema.isna().all()
    print("✅ EMA 测试通过")


def test_macd():
    """测试 MACD 计算"""
    np.random.seed(42)
    close = pd.Series(np.random.uniform(100, 110, 100).cumsum() / 10)
    
    dif, dea, macd_hist = calculate_macd(close)
    
    assert len(dif) == 100
    assert len(dea) == 100
    assert len(macd_hist) == 100
    print("✅ MACD 测试通过")


def test_rsi():
    """测试 RSI 计算"""
    close = pd.Series([50, 51, 52, 51, 50, 49, 48, 49, 50, 51])
    rsi = calculate_rsi(close, 5)
    
    assert len(rsi) == 10
    assert all((rsi.dropna() >= 0) & (rsi.dropna() <= 100))
    print("✅ RSI 测试通过")


if __name__ == "__main__":
    test_sma()
    test_ema()
    test_macd()
    test_rsi()
    print("\n✅ 所有指标测试通过！")
