"""
visualization.py - Matplotlib 量化可视化
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def plot_candlestick(df: pd.DataFrame, title: str = "K 线图"):
    """绘制 K 线图"""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for i in range(len(df)):
        o, c, h, l = df['open'].iloc[i], df['close'].iloc[i], df['high'].iloc[i], df['low'].iloc[i]
        color = 'red' if c >= o else 'green'
        ax.vlines(i, l, h, color=color, linewidth=1)
        rect = Rectangle((i - 0.3, min(o, c)), 0.6, abs(c - o), facecolor=color, edgecolor=color)
        ax.add_patch(rect)
    
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return fig

def plot_cumulative_return(returns: pd.Series):
    """绘制累计收益曲线"""
    fig, ax = plt.subplots(figsize=(14, 7))
    cum_return = (1 + returns).cumprod() - 1
    ax.plot(cum_return.index, cum_return * 100, linewidth=2)
    ax.set_title("累计收益曲线")
    ax.set_ylabel("收益率 (%)")
    ax.axhline(0, color='black', linewidth=0.5)
    ax.grid(True, alpha=0.3)
    return fig

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    close = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 100))
    
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, 100)),
        'high': close * (1 + np.random.uniform(0, 0.02, 100)),
        'low': close * (1 - np.random.uniform(0, 0.02, 100)),
        'close': close,
        'volume': np.random.randint(10000, 100000, 100)
    }, index=dates)
    
    fig1 = plot_candlestick(df.head(30))
    plt.savefig("candlestick.png", dpi=150)
    
    fig2 = plot_cumulative_return(df['close'].pct_change())
    plt.savefig("cumulative_return.png", dpi=150)
    
    print("✅ 图表已保存！")
