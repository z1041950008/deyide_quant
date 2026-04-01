"""
engine.py - 回测引擎

完整的回测框架，支持订单管理、绩效分析
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    BUY = 1
    SELL = -1


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2


@dataclass
class Order:
    """订单类"""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    order_type: OrderType = OrderType.MARKET
    timestamp: pd.Timestamp = None
    
    @property
    def value(self) -> float:
        return self.quantity * self.price


@dataclass
class Trade:
    """成交记录类"""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: pd.Timestamp
    commission: float


class Portfolio:
    """投资组合类"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}
        self.trades: List[Trade] = []
        self.history: List[Dict] = []
    
    def get_position(self, symbol: str) -> float:
        return self.positions.get(symbol, 0.0)
    
    def execute_order(
        self,
        order: Order,
        commission_rate: float = 0.001
    ) -> Optional[Trade]:
        """执行订单"""
        if order.side == OrderSide.BUY:
            cost = order.value * (1 + commission_rate)
            if cost > self.cash:
                return None
            
            self.cash -= cost
            self.positions[order.symbol] = self.positions.get(order.symbol, 0.0) + order.quantity
            
        else:  # SELL
            if self.get_position(order.symbol) < order.quantity:
                return None
            
            self.cash += order.value * (1 - commission_rate)
            self.positions[order.symbol] -= order.quantity
        
        commission = order.value * commission_rate
        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            timestamp=order.timestamp,
            commission=commission
        )
        self.trades.append(trade)
        
        return trade
    
    def record_snapshot(self, timestamp: pd.Timestamp, prices: Dict[str, float]):
        """记录组合快照"""
        market_value = sum(
            self.positions.get(symbol, 0) * price
            for symbol, price in prices.items()
        )
        total_value = self.cash + market_value
        
        self.history.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'market_value': market_value,
            'total_value': total_value
        })
    
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.history).set_index('timestamp')


class BacktestEngine:
    """
    回测引擎
    
    功能:
    - 订单管理
    - 组合管理
    - 绩效分析
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.portfolio = Portfolio(initial_capital)
        self.results: Optional[pd.DataFrame] = None
    
    def run(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        symbol: str = 'STOCK'
    ) -> pd.DataFrame:
        """
        运行回测
        
        参数:
            data: 包含 OHLCV 的 DataFrame
            signals: 交易信号 (1=买入，-1=卖出，0=持有)
            symbol: 标的代码
        
        返回:
            回测结果 DataFrame
        """
        self.portfolio = Portfolio(self.initial_capital)
        
        for i in range(len(data)):
            timestamp = data.index[i]
            row = data.iloc[i]
            signal = signals.iloc[i] if i < len(signals) else 0
            
            current_position = self.portfolio.get_position(symbol)
            
            # 生成订单
            if signal == 1 and current_position == 0:
                # 买入
                quantity = int(self.portfolio.cash * 0.95 / row['close'])
                if quantity > 0:
                    order = Order(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        price=row['close'] * (1 + self.slippage),
                        timestamp=timestamp
                    )
                    self.portfolio.execute_order(order, self.commission_rate)
            
            elif signal == -1 and current_position > 0:
                # 卖出
                order = Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=current_position,
                    price=row['close'] * (1 - self.slippage),
                    timestamp=timestamp
                )
                self.portfolio.execute_order(order, self.commission_rate)
            
            # 记录快照
            self.portfolio.record_snapshot(timestamp, {symbol: row['close']})
        
        self.results = self.portfolio.to_dataframe()
        return self.results
    
    def analyze(self) -> Dict:
        """
        绩效分析
        
        返回:
            绩效统计字典
        """
        if self.results is None:
            return {}
        
        df = self.results
        df['return'] = df['total_value'].pct_change()
        
        total_return = (df['total_value'].iloc[-1] - self.initial_capital) / self.initial_capital
        days = (df.index[-1] - df.index[0]).days
        
        annual_return = (1 + total_return) ** (365 / days) - 1
        volatility = df['return'].std() * np.sqrt(252)
        sharpe = (annual_return - 0.03) / volatility if volatility > 0 else 0
        
        cum_ret = df['total_value'] / self.initial_capital
        cum_max = cum_ret.cummax()
        max_drawdown = ((cum_ret - cum_max) / cum_max).min()
        
        # 交易统计
        trades = len(self.portfolio.trades)
        buy_trades = [t for t in self.portfolio.trades if t.side == OrderSide.BUY]
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': df['total_value'].iloc[-1],
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'total_trades': trades,
            'total_commission': sum(t.commission for t in self.portfolio.trades)
        }
    
    def plot_results(self):
        """绘制回测结果"""
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(3, 1, figsize=(14, 10))
            
            # 组合价值
            axes[0].plot(self.results.index, self.results['total_value'])
            axes[0].set_title('Portfolio Value')
            axes[0].set_ylabel('Value')
            axes[0].grid(True, alpha=0.3)
            
            # 累计收益
            cum_ret = (self.results['total_value'] / self.initial_capital - 1) * 100
            axes[1].plot(self.results.index, cum_ret)
            axes[1].set_title('Cumulative Return (%)')
            axes[1].set_ylabel('Return %')
            axes[1].grid(True, alpha=0.3)
            
            # 回撤
            cum_ret_norm = self.results['total_value'] / self.initial_capital
            drawdown = (cum_ret_norm - cum_ret_norm.cummax()) / cum_ret_norm.cummax() * 100
            axes[2].fill_between(self.results.index, drawdown, 0, alpha=0.5, color='red')
            axes[2].set_title('Drawdown (%)')
            axes[2].set_ylabel('Drawdown %')
            axes[2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('backtest_results.png')
            print("回测结果图已保存为 backtest_results.png")
            
        except ImportError:
            print("matplotlib 未安装，无法绘图")


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252)
    close = pd.Series(100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, 252)), index=dates)
    
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, 252)),
        'high': close * (1 + np.random.uniform(0, 0.02, 252)),
        'low': close * (1 - np.random.uniform(0, 0.02, 252)),
        'close': close,
        'volume': np.random.randint(10000, 100000, 252)
    })
    
    # 简单信号：均线金叉买入
    sma5 = close.rolling(5).mean()
    sma20 = close.rolling(20).mean()
    signals = pd.Series(0, index=dates)
    signals[(sma5 > sma20) & (sma5.shift(1) <= sma20.shift(1))] = 1
    signals[(sma5 < sma20) & (sma5.shift(1) >= sma20.shift(1))] = -1
    
    print("=" * 60)
    print("回测引擎示例")
    print("=" * 60)
    
    engine = BacktestEngine(initial_capital=100000, commission_rate=0.001)
    results = engine.run(df, signals)
    stats = engine.analyze()
    
    print("\n【回测绩效】")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}" if 'return' in key or 'drawdown' in key else f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ 回测完成！")
