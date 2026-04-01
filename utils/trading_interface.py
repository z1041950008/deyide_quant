"""
trading_interface.py - 实盘交易接口

模拟实盘交易接口，支持对接券商 API
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Order:
    """订单"""
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    status: str = 'PENDING'
    create_time: datetime = None
    fill_time: datetime = None
    fill_price: float = None


class TradingInterface:
    """
    交易接口基类
    
    功能:
    - 下单
    - 撤单
    - 查询持仓
    - 查询资金
    """
    
    def __init__(self, account_id: str = None):
        self.account_id = account_id
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, int] = {}
        self.cash = 100000.0
        self.order_counter = 0
    
    def generate_order_id(self) -> str:
        self.order_counter += 1
        return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{self.order_counter:04d}"
    
    def buy(self, symbol: str, quantity: int, price: float = None) -> Optional[str]:
        """
        买入
        
        参数:
            symbol: 股票代码
            quantity: 数量
            price: 价格 (None 为市价单)
        
        返回:
            订单 ID
        """
        order_id = self.generate_order_id()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            price=price or 0,
            create_time=datetime.now()
        )
        
        # 模拟成交
        order.status = 'FILLED'
        order.fill_time = datetime.now()
        order.fill_price = price or 100.0
        
        cost = order.fill_price * quantity * 1.001  # 含手续费
        if cost > self.cash:
            logger.warning(f"资金不足，买入失败")
            return None
        
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        
        self.orders[order_id] = order
        logger.info(f"买入成功：{symbol} x {quantity} @ {order.fill_price:.2f}")
        
        return order_id
    
    def sell(self, symbol: str, quantity: int, price: float = None) -> Optional[str]:
        """卖出"""
        if self.positions.get(symbol, 0) < quantity:
            logger.warning(f"持仓不足，卖出失败")
            return None
        
        order_id = self.generate_order_id()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side='SELL',
            quantity=quantity,
            price=price or 0,
            create_time=datetime.now()
        )
        
        order.status = 'FILLED'
        order.fill_time = datetime.now()
        order.fill_price = price or 100.0
        
        self.cash += order.fill_price * quantity * 0.999  # 扣除手续费
        self.positions[symbol] -= quantity
        
        self.orders[order_id] = order
        logger.info(f"卖出成功：{symbol} x {quantity} @ {order.fill_price:.2f}")
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == 'PENDING':
                order.status = 'CANCELLED'
                logger.info(f"订单已撤销：{order_id}")
                return True
        return False
    
    def get_position(self, symbol: str) -> int:
        """获取持仓"""
        return self.positions.get(symbol, 0)
    
    def get_positions(self) -> Dict[str, int]:
        """获取所有持仓"""
        return self.positions.copy()
    
    def get_cash(self) -> float:
        """获取可用资金"""
        return self.cash
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        total_value = self.cash + sum(
            self.positions.get(s, 0) * 100  # 假设价格 100
            for s in self.positions
        )
        
        return {
            'account_id': self.account_id,
            'cash': self.cash,
            'total_value': total_value,
            'num_positions': len(self.positions)
        }


class SimulatedTradingInterface(TradingInterface):
    """
    模拟交易接口
    
    用于回测和模拟交易
    """
    
    def __init__(self, account_id: str = None, initial_cash: float = 100000.0):
        super().__init__(account_id)
        self.cash = initial_cash
        self.price_history: Dict[str, List[float]] = {}
    
    def update_price(self, symbol: str, price: float):
        """更新价格"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        if symbol in self.price_history and self.price_history[symbol]:
            return self.price_history[symbol][-1]
        return None


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("实盘交易接口示例")
    print("=" * 60)
    
    trader = SimulatedTradingInterface(account_id='TEST001', initial_cash=100000)
    
    # 更新价格
    trader.update_price('000001', 50.0)
    
    # 买入
    order_id = trader.buy('000001', 1000, 50.0)
    print(f"\n订单 ID: {order_id}")
    
    # 查询持仓
    position = trader.get_position('000001')
    print(f"持仓：{position} 股")
    
    # 查询资金
    cash = trader.get_cash()
    print(f"可用资金：{cash:.2f}")
    
    # 账户信息
    info = trader.get_account_info()
    print("\n【账户信息】")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # 价格上涨后卖出
    trader.update_price('000001', 55.0)
    trader.sell('000001', 1000, 55.0)
    
    print(f"\n卖出后资金：{trader.get_cash():.2f}")
    
    print("\n✅ 交易接口示例完成！")
