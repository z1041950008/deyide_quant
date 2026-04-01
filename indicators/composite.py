"""
composite.py - 多指标组合应用

将多个技术指标组合使用，提高信号可靠性
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from .ma import calculate_sma, calculate_ema, detect_golden_cross
from .macd import calculate_macd, detect_macd_golden_cross
from .rsi import calculate_rsi, detect_oversold, detect_overbought
from .kdj import calculate_kdj, detect_kdj_golden_cross
from .boll import calculate_boll


class CompositeIndicator:
    """多指标组合分析器"""
    
    def __init__(self):
        self.signals = {}
    
    def calculate_all_indicators(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        计算所有常用指标
        
        参数:
            df: 包含 OHLCV 数据的 DataFrame
        
        返回:
            添加指标后的 DataFrame
        """
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # 移动平均线
        df['sma20'] = calculate_sma(close, 20)
        df['sma60'] = calculate_sma(close, 60)
        df['ema12'] = calculate_ema(close, 12)
        df['ema26'] = calculate_ema(close, 26)
        
        # MACD
        dif, dea, macd_hist = calculate_macd(close)
        df['dif'] = dif
        df['dea'] = dea
        df['macd_hist'] = macd_hist
        
        # RSI
        df['rsi14'] = calculate_rsi(close, 14)
        
        # KDJ
        k, d, j = calculate_kdj(high, low, close)
        df['kdj_k'] = k
        df['kdj_d'] = d
        df['kdj_j'] = j
        
        # 布林带
        middle, upper, lower, bandwidth = calculate_boll(close)
        df['boll_middle'] = middle
        df['boll_upper'] = upper
        df['boll_lower'] = lower
        
        return df
    
    def ma_macd_strategy(self, df: pd.DataFrame) -> pd.Series:
        """
        MA + MACD 组合策略
        
        买入条件:
        1. 短期均线上穿长期均线 (金叉)
        2. MACD 金叉
        
        参数:
            df: 包含指标的 DataFrame
        
        返回:
            买入信号序列
        """
        # MA 金叉
        ma_golden = detect_golden_cross(df['sma20'], df['sma60'])
        
        # MACD 金叉
        macd_golden = detect_macd_golden_cross(df['dif'], df['dea'])
        
        # 同时满足两个条件
        signal = (ma_golden == 1) & (macd_golden == 1)
        
        return signal.astype(int)
    
    def rsi_kdj_strategy(self, df: pd.DataFrame) -> pd.Series:
        """
        RSI + KDJ 组合策略 (超买超卖)
        
        买入条件:
        1. RSI 超卖 (<30)
        2. KDJ 超卖 (K<20 且 D<20)
        
        参数:
            df: 包含指标的 DataFrame
        
        返回:
            买入信号序列
        """
        # RSI 超卖
        rsi_oversold = detect_oversold(df['rsi14'], 30)
        
        # KDJ 超卖
        kdj_oversold = (df['kdj_k'] < 20) & (df['kdj_d'] < 20)
        
        # 同时满足
        signal = (rsi_oversold == 1) & kdj_oversold
        
        return signal.astype(int)
    
    def boll_rsi_strategy(self, df: pd.DataFrame) -> pd.Series:
        """
        布林带 + RSI 组合策略
        
        买入条件:
        1. 价格触及或跌破布林带下轨
        2. RSI 超卖
        
        参数:
            df: 包含指标的 DataFrame
        
        返回:
            买入信号序列
        """
        # 价格触及下轨
        touch_lower = df['close'] <= df['boll_lower']
        
        # RSI 超卖
        rsi_oversold = detect_oversold(df['rsi14'], 30)
        
        signal = touch_lower & (rsi_oversold == 1)
        
        return signal.astype(int)
    
    def generate_composite_signal(
        self,
        df: pd.DataFrame,
        weights: Dict[str, float] = None
    ) -> pd.Series:
        """
        生成综合信号 (加权评分)
        
        参数:
            df: 包含指标的 DataFrame
            weights: 各指标权重
        
        返回:
            综合评分序列 (-1 到 1)
        """
        if weights is None:
            weights = {
                'ma': 0.2,
                'macd': 0.2,
                'rsi': 0.2,
                'kdj': 0.2,
                'boll': 0.2
            }
        
        score = pd.Series(0.0, index=df.index)
        
        # MA 评分
        ma_score = pd.Series(0, index=df.index)
        ma_score[df['sma20'] > df['sma60']] = 1
        ma_score[df['sma20'] < df['sma60']] = -1
        score += weights['ma'] * ma_score
        
        # MACD 评分
        macd_score = pd.Series(0, index=df.index)
        macd_score[df['dif'] > df['dea']] = 1
        macd_score[df['dif'] < df['dea']] = -1
        score += weights['macd'] * macd_score
        
        # RSI 评分
        rsi_score = pd.Series(0, index=df.index)
        rsi_score[df['rsi14'] < 30] = 1  # 超卖看涨
        rsi_score[df['rsi14'] > 70] = -1  # 超买卖出
        score += weights['rsi'] * rsi_score
        
        # KDJ 评分
        kdj_score = pd.Series(0, index=df.index)
        kdj_score[df['kdj_k'] > df['kdj_d']] = 1
        kdj_score[df['kdj_k'] < df['kdj_d']] = -1
        score += weights['kdj'] * kdj_score
        
        # 布林带评分
        boll_score = pd.Series(0, index=df.index)
        boll_score[df['close'] < df['boll_lower']] = 1
        boll_score[df['close'] > df['boll_upper']] = -1
        score += weights['boll'] * boll_score
        
        return score
    
    def get_strategy_summary(self, df: pd.DataFrame) -> Dict:
        """
        获取各策略信号汇总
        
        参数:
            df: 包含指标的 DataFrame
        
        返回:
            信号汇总字典
        """
        summary = {}
        
        # MA+MACD
        ma_macd = self.ma_macd_strategy(df)
        summary['ma_macd_buy'] = ma_macd.sum()
        
        # RSI+KDJ
        rsi_kdj = self.rsi_kdj_strategy(df)
        summary['rsi_kdj_buy'] = rsi_kdj.sum()
        
        # Boll+RSI
        boll_rsi = self.boll_rsi_strategy(df)
        summary['boll_rsi_buy'] = boll_rsi.sum()
        
        # 综合评分
        composite = self.generate_composite_signal(df)
        summary['avg_composite_score'] = composite.mean()
        summary['strong_buy'] = (composite > 0.5).sum()
        summary['strong_sell'] = (composite < -0.5).sum()
        
        return summary


# ==================== 使用示例 ====================

if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100)
    
    base = np.random.uniform(10, 20, 100).cumsum() / 10
    df = pd.DataFrame({
        'open': base + np.random.uniform(-0.5, 0.5, 100),
        'high': base + np.random.uniform(0, 1, 100),
        'low': base - np.random.uniform(0, 1, 100),
        'close': base + np.random.uniform(-0.5, 0.5, 100),
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    print("=" * 60)
    print("多指标组合应用示例")
    print("=" * 60)
    
    analyzer = CompositeIndicator()
    
    # 计算所有指标
    df_with_indicators = analyzer.calculate_all_indicators(df)
    
    print("\n【指标计算结果 - 前 10 行】")
    cols = ['close', 'sma20', 'sma60', 'dif', 'dea', 'rsi14', 'kdj_k', 'kdj_d']
    print(df_with_indicators[cols].round(2).head(10))
    
    # 获取策略汇总
    summary = analyzer.get_strategy_summary(df_with_indicators)
    
    print("\n【策略信号汇总】")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 综合评分
    composite_score = analyzer.generate_composite_signal(df_with_indicators)
    print(f"\n【最新综合评分】: {composite_score.iloc[-1]:.3f}")
    
    print("\n✅ 多指标组合分析完成！")
