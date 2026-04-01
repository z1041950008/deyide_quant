"""
macd_strategy.py - MACD 金叉死叉策略

基于 MACD 指标的趋势跟踪策略
"""
import numpy as np
import pandas as pd
from typing import Tuple
import sys
sys.path.insert(0, '..')
from indicators.macd import calculate_macd, detect_macd_golden_cross, detect_macd_death_cross


class MACDStrategy:
    """
    MACD 金叉死叉策略
    
    原理:
    - DIF 上穿 DEA -> 金叉 -> 买入
    - DIF 下穿 DEA -> 死叉 -> 卖出
    
    过滤条件:
    - 只在零轴上方金叉买入 (强势)
    - 只在零轴下方死叉卖出 (弱势)
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        zero_axis_filter: bool = True
    ):
        """
        初始化策略
        
        参数:
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            zero_axis_filter: 是否启用零轴过滤
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.zero_axis_filter = zero_axis_filter
        self.name = f"MACD({fast_period}/{slow_period}/{signal_period})"
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        参数:
            df: 包含 close 列的 DataFrame
        
        返回:
            包含信号列的 DataFrame
        """
        df = df.copy()
        close = df['close']
        
        # 计算 MACD
        dif, dea, macd_hist = calculate_macd(
            close,
            self.fast_period,
            self.slow_period,
            self.signal_period
        )
        
        df['dif'] = dif
        df['dea'] = dea
        df['macd_hist'] = macd_hist
        
        # 生成金叉死叉信号
        golden = detect_macd_golden_cross(dif, dea)
        death = detect_macd_death_cross(dif, dea)
        
        # 应用零轴过滤
        if self.zero_axis_filter:
            # 零轴上方金叉
            golden = golden & (dif > 0)
            # 零轴下方死叉
            death = death & (dif < 0)
        
        df['golden_cross'] = golden
        df['death_cross'] = death
        
        # 持仓信号
        df['position'] = 0
        df.loc[golden == 1, 'position'] = 1
        df.loc[death == 1, 'position'] = -1
        df['position'] = df['position'].replace(0, np.nan).ffill().fillna(0)
        
        return df
    
    def backtest(
        self,
        df: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission: float = 0.001
    ) -> Tuple[pd.DataFrame, dict]:
        """简单回测"""
        df = self.generate_signals(df)
        
        df['return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'].shift(1) * df['return']
        df['turnover'] = df['position'].diff().abs()
        df['strategy_return'] = df['strategy_return'] - df['turnover'] * commission
        
        df['cum_return'] = (1 + df['return']).cumprod() - 1
        df['cum_strategy_return'] = (1 + df['strategy_return']).cumprod() - 1
        
        total_return = df['cum_strategy_return'].iloc[-1]
        days = (df.index[-1] - df.index[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1
        volatility = df['strategy_return'].std() * np.sqrt(252)
        sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0
        
        cum_ret = (1 + df['strategy_return']).cumprod()
        max_drawdown = ((cum_ret - cum_ret.cummax()) / cum_ret.cummax()).min()
        
        trades = df['position'].diff().abs()
        trade_returns = df['strategy_return'][trades > 0]
        win_rate = (trade_returns > 0).sum() / len(trade_returns) if len(trade_returns) > 0 else 0
        
        stats = {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': trades.sum()
        }
        
        return df, stats


if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252)
    base = 100
    returns = np.random.normal(0.0005, 0.02, 252)
    close = pd.Series(base * np.cumprod(1 + returns), index=dates)
    
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, 252)),
        'high': close * (1 + np.random.uniform(0, 0.02, 252)),
        'low': close * (1 - np.random.uniform(0, 0.02, 252)),
        'close': close,
        'volume': np.random.randint(10000, 100000, 252)
    })
    
    print("=" * 60)
    print("MACD 策略回测示例")
    print("=" * 60)
    
    strategy = MACDStrategy()
    result, stats = strategy.backtest(df)
    
    print("\n【策略绩效统计】")
    print(f"  总收益率：{stats['total_return']:.2%}")
    print(f"  年化收益：{stats['annual_return']:.2%}")
    print(f"  夏普比率：{stats['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{stats['max_drawdown']:.2%}")
    print(f"  胜率：{stats['win_rate']:.2%}")
    print(f"  交易次数：{stats['total_trades']}")
    
    print("\n✅ MACD 策略回测完成！")
