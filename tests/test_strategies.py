"""
test_strategies.py - 策略模块单元测试
"""
import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, '..')

from strategy.dual_ma import DualMAStrategy
from strategy.macd_strategy import MACDStrategy


def generate_test_data(n=252):
    """生成测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=n)
    close = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, n))
    
    return pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, n)),
        'high': close * (1 + np.random.uniform(0, 0.02, n)),
        'low': close * (1 - np.random.uniform(0, 0.02, n)),
        'close': close,
        'volume': np.random.randint(10000, 100000, n)
    }, index=dates)


def test_dual_ma():
    """测试双均线策略"""
    df = generate_test_data()
    strategy = DualMAStrategy(short_window=5, long_window=20)
    
    result, stats = strategy.backtest(df)
    
    assert 'sma_short' in result.columns
    assert 'sma_long' in result.columns
    assert 'position' in result.columns
    assert 'total_return' in stats
    print("✅ 双均线策略测试通过")


def test_macd_strategy():
    """测试 MACD 策略"""
    df = generate_test_data()
    strategy = MACDStrategy()
    
    result, stats = strategy.backtest(df)
    
    assert 'dif' in result.columns
    assert 'dea' in result.columns
    assert 'total_return' in stats
    print("✅ MACD 策略测试通过")


if __name__ == "__main__":
    test_dual_ma()
    test_macd_strategy()
    print("\n✅ 所有策略测试通过！")
