"""
dual_ma.py - 双均线策略

最经典的趋势跟踪策略
"""
import numpy as np
import pandas as pd
from typing import Tuple
import sys
sys.path.insert(0, '..')
from indicators.ma import calculate_sma, detect_golden_cross, detect_death_cross


class DualMAStrategy:
    """
    双均线策略
    
    原理:
    - 短期均线上穿长期均线 -> 金叉 -> 买入
    - 短期均线下穿长期均线 -> 死叉 -> 卖出
    """
    
    def __init__(
        self,
        short_window: int = 5,
        long_window: int = 20
    ):
        """
        初始化策略
        
        参数:
            short_window: 短期均线周期
            long_window: 长期均线周期
        """
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"DualMA({short_window}/{long_window})"
    
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
        
        # 计算均线
        df['sma_short'] = calculate_sma(close, self.short_window)
        df['sma_long'] = calculate_sma(close, self.long_window)
        
        # 生成信号
        df['golden_cross'] = detect_golden_cross(df['sma_short'], df['sma_long'])
        df['death_cross'] = detect_death_cross(df['sma_short'], df['sma_long'])
        
        # 持仓信号：1=多头，0=空仓，-1=空头
        df['position'] = 0
        df.loc[df['golden_cross'] == 1, 'position'] = 1
        df.loc[df['death_cross'] == 1, 'position'] = -1
        df['position'] = df['position'].replace(0, np.nan).ffill().fillna(0)
        
        return df
    
    def backtest(
        self,
        df: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission: float = 0.001
    ) -> Tuple[pd.DataFrame, dict]:
        """
        简单回测
        
        参数:
            df: 包含 OHLCV 数据的 DataFrame
            initial_capital: 初始资金
            commission: 手续费率
        
        返回:
            (回测结果 DataFrame, 绩效统计字典)
        """
        # 生成信号
        df = self.generate_signals(df)
        
        # 计算策略收益
        df['return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'].shift(1) * df['return']
        
        # 扣除手续费
        df['turnover'] = df['position'].diff().abs()
        df['strategy_return'] = df['strategy_return'] - df['turnover'] * commission
        
        # 计算累计收益
        df['cum_return'] = (1 + df['return']).cumprod() - 1
        df['cum_strategy_return'] = (1 + df['strategy_return']).cumprod() - 1
        
        # 计算绩效指标
        total_return = df['cum_strategy_return'].iloc[-1]
        
        # 年化收益
        days = (df.index[-1] - df.index[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # 波动率
        volatility = df['strategy_return'].std() * np.sqrt(252)
        
        # 夏普比率
        risk_free = 0.03
        sharpe = (annual_return - risk_free) / volatility if volatility > 0 else 0
        
        # 最大回撤
        cum_ret = (1 + df['strategy_return']).cumprod()
        cum_max = cum_ret.cummax()
        drawdown = (cum_ret - cum_max) / cum_max
        max_drawdown = drawdown.min()
        
        # 胜率
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


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252)  # 一年交易日
    
    # 生成模拟股价
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
    print("双均线策略回测示例")
    print("=" * 60)
    
    strategy = DualMAStrategy(short_window=5, long_window=20)
    result, stats = strategy.backtest(df)
    
    print("\n【策略绩效统计】")
    print(f"  总收益率：{stats['total_return']:.2%}")
    print(f"  年化收益：{stats['annual_return']:.2%}")
    print(f"  波动率：{stats['volatility']:.2%}")
    print(f"  夏普比率：{stats['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{stats['max_drawdown']:.2%}")
    print(f"  胜率：{stats['win_rate']:.2%}")
    print(f"  交易次数：{stats['total_trades']}")
    
    print("\n【最后 10 天数据】")
    print(result[['close', 'sma_short', 'sma_long', 'position', 'strategy_return']].tail(10).round(4))
    
    print("\n✅ 双均线策略回测完成！")
