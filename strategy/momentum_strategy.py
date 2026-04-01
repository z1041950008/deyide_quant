"""
momentum_strategy.py - 动量策略

基于价格动量效应的趋势跟踪策略
"""
import numpy as np
import pandas as pd
from typing import Tuple


class MomentumStrategy:
    """
    动量策略
    
    原理:
    - 过去 N 日涨幅排名前 -> 买入
    - 持有 M 天后调仓
    """
    
    def __init__(self, lookback: int = 20, holding_period: int = 20):
        self.lookback = lookback
        self.holding_period = holding_period
        self.name = f"Momentum({lookback}/{holding_period})"
    
    def calculate_momentum(self, close: pd.Series) -> pd.Series:
        """计算动量"""
        return close.pct_change(self.lookback)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        momentum = self.calculate_momentum(df['close'])
        df['momentum'] = momentum
        
        df['position'] = 0
        df.loc[momentum > 0.1, 'position'] = 1  # 动量>10% 买入
        df.loc[momentum < -0.1, 'position'] = -1  # 动量<-10% 卖出
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
    
    print("动量策略回测")
    strategy = MomentumStrategy()
    result, stats = strategy.backtest(df)
    
    print(f"总收益：{stats['total_return']:.2%}")
    print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
