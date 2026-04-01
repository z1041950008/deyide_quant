"""
boll_strategy.py - 布林带突破策略

基于布林带的趋势跟踪策略
"""
import numpy as np
import pandas as pd
from typing import Tuple
import sys
sys.path.insert(0, '..')
from indicators.boll import calculate_boll, detect_breakout


class BollStrategy:
    """
    布林带突破策略
    
    原理:
    - 价格上穿上轨 -> 买入 (突破)
    - 价格下穿下轨 -> 卖出 (突破)
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std
        self.name = f"Boll({window}/{num_std})"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        close = df['close']
        
        middle, upper, lower, _ = calculate_boll(close, self.window, self.num_std)
        
        df['boll_upper'] = upper
        df['boll_lower'] = lower
        df['boll_middle'] = middle
        
        breakout_up, breakout_down = detect_breakout(close, upper, lower)
        
        df['position'] = 0
        df.loc[breakout_up == 1, 'position'] = 1
        df.loc[breakout_down == 1, 'position'] = -1
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
    
    print("布林带策略回测")
    strategy = BollStrategy()
    result, stats = strategy.backtest(df)
    
    print(f"总收益：{stats['total_return']:.2%}")
    print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
