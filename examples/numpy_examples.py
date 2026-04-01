"""
numpy_examples.py - NumPy 量化计算示例
"""
import numpy as np
import pandas as pd

def array_operations():
    """数组基础操作"""
    print("=" * 60)
    print("1. 数组创建与操作")
    print("=" * 60)
    
    prices = np.array([100, 102, 101, 105, 108, 107, 110])
    print(f"\n价格数组：{prices}")
    print(f"形状：{prices.shape}")
    print(f"维度：{prices.ndim}")
    
    returns = np.diff(prices) / prices[:-1]
    print(f"\n收益率：{returns}")
    
    return prices

def vectorized_calculation(prices: np.ndarray):
    """向量化计算示例"""
    print("\n" + "=" * 60)
    print("2. 向量化计算")
    print("=" * 60)
    
    cum_return = np.cumprod(1 + np.diff(prices) / prices[:-1]) - 1
    print(f"\n累计收益率：{cum_return}")
    
    window = 3
    ma = np.convolve(prices, np.ones(window)/window, mode='valid')
    print(f"{window}日移动平均：{ma}")
    
    return cum_return

def statistical_functions(prices: np.ndarray):
    """统计函数应用"""
    print("\n" + "=" * 60)
    print("3. 统计函数")
    print("=" * 60)
    
    returns = np.diff(prices) / prices[:-1]
    
    print(f"\n收益率均值：{np.mean(returns):.6f}")
    print(f"收益率标准差：{np.std(returns):.6f}")
    print(f"最小值：{np.min(returns):.6f}")
    print(f"最大值：{np.max(returns):.6f}")

def quant_applications():
    """量化应用实例"""
    print("\n" + "=" * 60)
    print("4. 量化应用实例")
    print("=" * 60)
    
    np.random.seed(42)
    n_days = 252
    daily_return = np.random.normal(0.0005, 0.02, n_days)
    prices = 100 * np.cumprod(1 + daily_return)
    
    cum_max = np.maximum.accumulate(prices)
    drawdown = (prices - cum_max) / cum_max
    max_drawdown = np.min(drawdown)
    print(f"\n最大回撤：{max_drawdown:.2%}")
    
    risk_free = 0.03 / 252
    sharpe = (np.mean(daily_return) - risk_free) / np.std(daily_return) * np.sqrt(252)
    print(f"夏普比率：{sharpe:.2f}")

if __name__ == "__main__":
    prices = array_operations()
    vectorized_calculation(prices)
    statistical_functions(prices)
    quant_applications()
    print("\n✅ NumPy 示例完成！")
