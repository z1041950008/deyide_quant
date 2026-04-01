"""
risk_manager.py - 风险管理模块

仓位管理、止损止盈、回撤控制
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    
    @property
    def pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def pnl_percent(self) -> float:
        return (self.current_price - self.entry_price) / self.entry_price


class RiskManager:
    """
    风险管理器
    
    功能:
    - 仓位管理
    - 止损止盈
    - 回撤控制
    - 风险指标计算
    """
    
    def __init__(
        self,
        total_capital: float = 100000.0,
        max_position_pct: float = 0.2,
        max_total_exposure: float = 0.8,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15,
        max_drawdown_pct: float = 0.2
    ):
        """
        初始化风险管理器
        
        参数:
            total_capital: 总资金
            max_position_pct: 单只股票最大仓位比例
            max_total_exposure: 最大总仓位比例
            stop_loss_pct: 止损比例
            take_profit_pct: 止盈比例
            max_drawdown_pct: 最大回撤限制
        """
        self.total_capital = total_capital
        self.max_position_pct = max_position_pct
        self.max_total_exposure = max_total_exposure
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_drawdown_pct = max_drawdown_pct
        
        self.positions: Dict[str, Position] = {}
        self.peak_value = total_capital
        self.current_value = total_capital
    
    def calculate_position_size(self, price: float) -> int:
        """
        计算仓位大小
        
        参数:
            price: 当前价格
        
        返回:
            可购买股数
        """
        max_position_value = self.total_capital * self.max_position_pct
        quantity = int(max_position_value / price / 100) * 100  # 100 股整数倍
        return quantity
    
    def check_total_exposure(self) -> float:
        """检查总仓位"""
        total_exposure = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )
        return total_exposure / self.total_capital
    
    def can_open_position(self, price: float) -> bool:
        """
        检查是否可以开新仓
        
        参数:
            price: 当前价格
        
        返回:
            是否可以开仓
        """
        current_exposure = self.check_total_exposure()
        new_position_value = self.calculate_position_size(price) * price
        
        if current_exposure + new_position_value / self.total_capital > self.max_total_exposure:
            return False
        
        if self.current_value < self.peak_value * (1 - self.max_drawdown_pct):
            return False
        
        return True
    
    def open_position(
        self,
        symbol: str,
        quantity: float,
        price: float
    ) -> Optional[Position]:
        """
        开仓
        
        参数:
            symbol: 股票代码
            quantity: 数量
            price: 价格
        
        返回:
            持仓对象
        """
        stop_loss = price * (1 - self.stop_loss_pct)
        take_profit = price * (1 + self.take_profit_pct)
        
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        return position
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
        
        self.current_value = sum(
            pos.quantity * pos.current_price
            for pos in self.positions.values()
        )
        
        if self.current_value > self.peak_value:
            self.peak_value = self.current_value
    
    def check_stop_loss(self, symbol: str) -> Optional[str]:
        """
        检查止损
        
        参数:
            symbol: 股票代码
        
        返回:
            需要止损的股票代码
        """
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        
        if pos.current_price <= pos.stop_loss:
            return symbol
        
        return None
    
    def check_take_profit(self, symbol: str) -> Optional[str]:
        """检查止盈"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        
        if pos.current_price >= pos.take_profit:
            return symbol
        
        return None
    
    def close_position(self, symbol: str) -> Optional[Position]:
        """平仓"""
        if symbol in self.positions:
            pos = self.positions.pop(symbol)
            return pos
        return None
    
    def get_risk_metrics(self) -> Dict:
        """获取风险指标"""
        if not self.positions:
            return {}
        
        total_pnl = sum(pos.pnl for pos in self.positions.values())
        total_pnl_pct = total_pnl / self.total_capital
        
        current_exposure = self.check_total_exposure()
        current_drawdown = (self.peak_value - self.current_value) / self.peak_value
        
        return {
            'total_capital': self.total_capital,
            'current_value': self.current_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_pct,
            'current_exposure': current_exposure,
            'current_drawdown': current_drawdown,
            'peak_value': self.peak_value,
            'num_positions': len(self.positions)
        }


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("风险管理器示例")
    print("=" * 60)
    
    rm = RiskManager(
        total_capital=100000,
        max_position_pct=0.2,
        stop_loss_pct=0.05,
        take_profit_pct=0.15
    )
    
    # 开仓
    price = 50.0
    if rm.can_open_position(price):
        quantity = rm.calculate_position_size(price)
        pos = rm.open_position('000001', quantity, price)
        print(f"\n开仓：{pos.symbol}, 数量：{pos.quantity}, 价格：{pos.entry_price}")
        print(f"止损位：{pos.stop_loss:.2f}, 止盈位：{pos.take_profit:.2f}")
    
    # 更新价格
    rm.update_prices({'000001': 52.0})
    
    # 检查止损止盈
    sl = rm.check_stop_loss('000001')
    tp = rm.check_take_profit('000001')
    print(f"\n止损检查：{sl}, 止盈检查：{tp}")
    
    # 风险指标
    metrics = rm.get_risk_metrics()
    print("\n【风险指标】")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ 风险管理示例完成！")
