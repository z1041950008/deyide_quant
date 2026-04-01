"""
volume_strategy.py - 成交量放大策略

基于成交量变化的趋势跟踪策略
"""
import numpy as np
import pandas as pd
from typing import Tuple
import sys
sys.path.insert(0, '..')
from indicators.volume import calculate_volume_ratio, detect_volume_spike


class VolumeStrategy:
    """
    成交量放大策略
    
    原理:
    - 量比 > 2 且价格上涨 -> 买入
    - 量比 < 0.5 且价格下跌 -> 卖出
    """
    
    def __init__(self, volume_window: int = 5, volume_threshold: float = 2.0):
        self.volume_window = volume_window
        self.volume_threshold = volume_threshold
        self.name = f"Volume({volume_window}/{volume_threshold})"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        vol_ratio = calculate_volume_ratio(df['volume'], self.volume_window)
        df['volume_ratio'] = vol_ratio
        
        price_change = df['close'].pct_change()
        
        df['position'] = 0
        df.loc[(vol_ratio > self.volume_threshold) & (price_change > 0), 'position'] = 1
        df.loc[(vol_ratio < 0.5) & (price_change < 0), 'position'] = -1
        df['position'] = df['position'].replace(0, np.nan).ffill().fillna(0)
        
        return df
    
    def backtest(self, df: pd.DataFrame, commission: float = 0.001) -> Tuple[pd.DataFrame, dict]:
        df = self.generate_signals(df)
        
        df['return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'].shift(1) * df['return'] - df['position'].diff().abs() * commission
        df['cum_strategy_return'] = (1 + df['strategy_return']).cumprod() - 1
        
        total_return = df['cum_strategy_return'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1
        volatility = df['strategy_return'].std() * np.sqrt(252)
        sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0
        
        cum_ret = (1 + df['strategy_return']).cumprod()
        max_drawdown = ((cum_ret - cum_ret.cummax()) / cum_ret.cummax()).min()
        
        stats = {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'total_trades': df['position'].diff().abs().sum()
        }
        
        return df, stats


if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252)
    close = pd.Series(100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, 252)), index=dates)
    
    df = pd.DataFrame({'close': close, 'volume': np.random.randint(10000, 100000, 252)})
    
    print("成交量策略回测")
    strategy = VolumeStrategy()
    result, stats = strategy.backtest(df)
    
    print(f"总收益：{stats['total_return']:.2%}")
    print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
