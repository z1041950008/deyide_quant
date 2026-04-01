"""
rsi_strategy.py - RSI 超买超卖策略

基于 RSI 指标的均值回归策略
"""
import numpy as np
import pandas as pd
from typing import Tuple
import sys
sys.path.insert(0, '..')
from indicators.rsi import calculate_rsi, detect_oversold, detect_overbought


class RSIStrategy:
    """
    RSI 超买超卖策略
    
    原理:
    - RSI < 30 (超卖) -> 买入
    - RSI > 70 (超买) -> 卖出
    
    适用于震荡市
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        oversold_threshold: float = 30,
        overbought_threshold: float = 70
    ):
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        self.name = f"RSI({rsi_period})"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        close = df['close']
        
        df['rsi'] = calculate_rsi(close, self.rsi_period)
        
        oversold = detect_oversold(df['rsi'], self.oversold_threshold)
        overbought = detect_overbought(df['rsi'], self.overbought_threshold)
        
        df['position'] = 0
        df.loc[oversold == 1, 'position'] = 1
        df.loc[overbought == 1, 'position'] = -1
        df['position'] = df['position'].replace(0, np.nan).ffill().fillna(0)
        
        return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 100000.0, commission: float = 0.001) -> Tuple[pd.DataFrame, dict]:
        df = self.generate_signals(df)
        
        df['return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'].shift(1) * df['return']
        df['turnover'] = df['position'].diff().abs()
        df['strategy_return'] = df['strategy_return'] - df['turnover'] * commission
        
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
    close = pd.Series(100 * np.cumprod(1 + np.random.normal(0, 0.02, 252)), index=dates)
    
    df = pd.DataFrame({'close': close, 'volume': np.random.randint(10000, 100000, 252)})
    
    print("RSI 策略回测")
    strategy = RSIStrategy()
    result, stats = strategy.backtest(df)
    
    print(f"总收益：{stats['total_return']:.2%}")
    print(f"夏普比率：{stats['sharpe_ratio']:.2f}")
    print(f"最大回撤：{stats['max_drawdown']:.2%}")
