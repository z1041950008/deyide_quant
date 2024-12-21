import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
import akshare as ak 
from datetime import datetime

# https://github.com/z1041950008/deyide_quant
# 如果需要定制化开发，可以私信我
# 如果觉得不错，可以点个star，谢谢
# 后续会更新更多指标，敬请期待
class PatternAnalyser:
    def __init__(self, data: pd.DataFrame):

        self.data = data
        self.patterns = {}
  
    # 分析所有可能的形态
    def analyse_all_patterns(self) -> Dict[str, Dict]:
        
        results = {}
        
        # 添加所有形态检测
        results.update(self._check_head_and_shoulders())
        results.update(self._check_double_top_bottom())
        results.update(self._check_triangle())
        results.update(self._check_flag_patterns())
        results.update(self._check_wedge_patterns())
       
        return results

    # 头肩顶/底形态检测
    def _check_head_and_shoulders(self) -> Dict[str, Dict]:
      
        result = {}
        prices = self.data['close'].values
        n = len(prices)
        
        if n >= 40:
            window = 40
            for i in range(len(prices) - window):
                segment = prices[i:i+window]
                
                # 寻找局部极值点
                peaks = []
                for j in range(1, len(segment)-1):
                    if segment[j] > segment[j-1] and segment[j] > segment[j+1]:
                        peaks.append((j, segment[j]))
                
                if len(peaks) >= 3:
                    # 检查三个峰值的相对位置和高度
                    left_shoulder = peaks[0][1]
                    head = peaks[1][1]
                    right_shoulder = peaks[2][1]
                    
                    # 计算颈线水平
                    neckline = min(prices[i+peaks[0][0]:i+peaks[1][0]].min(),
                                 prices[i+peaks[1][0]:i+peaks[2][0]].min())
                    
                    # 头肩顶条件
                    if (head > left_shoulder and head > right_shoulder and
                        abs(left_shoulder - right_shoulder) / head < 0.1 and
                        left_shoulder > neckline and right_shoulder > neckline):
                        
                        result['HEAD_AND_SHOULDERS_TOP'] = {
                            'type': 'bearish',
                            'confidence': 0.8,
                            'description': '形成完整头肩顶形态，强烈看跌信号'
                        }
                    
                    # 添加头肩底条件
                    elif (head < left_shoulder and head < right_shoulder and
                          abs(left_shoulder - right_shoulder) / left_shoulder < 0.1 and
                          left_shoulder < neckline and right_shoulder < neckline):
                        
                        result['HEAD_AND_SHOULDERS_BOTTOM'] = {
                            'type': 'bullish',
                            'confidence': 0.8,
                            'description': '形成完整头肩底形态，强烈看涨信号'
                        }

        return result

    # 双顶/双底形态检测
    def _check_double_top_bottom(self) -> Dict[str, Dict]:
        result = {}
        prices = self.data['close'].values
        n = len(prices)
        
        if n >= 20:
            # 双顶检测逻辑
            first_peak = max(prices[0:10])
            second_peak = max(prices[10:20])
            
            if abs(first_peak - second_peak) / first_peak < 0.05:
                result['DOUBLE_TOP'] = {
                    'type': 'bearish',
                    'confidence': 0.6,
                    'description': '可能形成双顶形态，看跌信号'
                }
            
            # 添加双底检测逻辑
            first_bottom = min(prices[0:10])
            second_bottom = min(prices[10:20])
            
            if abs(first_bottom - second_bottom) / first_bottom < 0.05:
                result['DOUBLE_BOTTOM'] = {
                    'type': 'bullish',
                    'confidence': 0.6,
                    'description': '可能形成双底形态，看涨信号'
                }
                
        return result
    # 双顶/双底形态检测
    def _check_double_top_bottom(self) -> Dict[str, Dict]:
        result = {}
        prices = self.data['close'].values
        n = len(prices)
        
        if n >= 20:
            # 双顶检测逻辑
            first_peak = max(prices[0:10])
            second_peak = max(prices[10:20])
            
            if abs(first_peak - second_peak) / first_peak < 0.05:
                result['DOUBLE_TOP'] = {
                    'type': 'bearish',
                    'confidence': 0.6,
                    'description': '可能形成双顶形态，看跌信号'
                }
            
            # 添加双底检测逻辑
            first_bottom = min(prices[0:10])
            second_bottom = min(prices[10:20])
            
            if abs(first_bottom - second_bottom) / first_bottom < 0.05:
                result['DOUBLE_BOTTOM'] = {
                    'type': 'bullish',
                    'confidence': 0.6,
                    'description': '可能形成双底形态，看涨信号'
                }
                
        return result

    def _check_triangle(self) -> Dict[str, Dict]:
        """检测三角形形态"""
        result = {}
        highs = self.data['high'].values
        lows = self.data['low'].values
        n = len(highs)
        
        if n >= 20:
            # 对称三角形检测逻辑
            high_slope = np.polyfit(range(20), highs[-20:], 1)[0]
            low_slope = np.polyfit(range(20), lows[-20:], 1)[0]
            
            if abs(high_slope) < 0.01 and abs(low_slope) < 0.01:
                result['SYMMETRIC_TRIANGLE'] = {
                    'type': 'neutral',
                    'confidence': 0.5,
                    'description': '可能形成对称三角形，需要等待突破方向'
                }
                
        return result

    def _check_flag_patterns(self) -> Dict[str, Dict]:
        """检测旗形和三角旗形态"""
        result = {}
        prices = self.data['close'].values
        volumes = self.data['volume'].values
        n = len(prices)
        
        if n >= 20:
            # 检查前期是否有明显的趋势（旗杆）
            trend_period = prices[-20:-10]
            flag_period = prices[-10:]
            
            trend_slope = np.polyfit(range(10), trend_period, 1)[0]
            flag_slope = np.polyfit(range(10), flag_period, 1)[0]
            
            # 判断旗形
            if abs(trend_slope) > abs(flag_slope) * 3:  # 旗杆斜率显著大于旗形
                if trend_slope > 0:  # 上升旗形
                    result['BULL_FLAG'] = {
                        'type': 'bullish',
                        'confidence': 0.7,
                        'description': '形成上升旗形，看涨延续形态'
                    }
                else:  # 下降旗形
                    result['BEAR_FLAG'] = {
                        'type': 'bearish',
                        'confidence': 0.7,
                        'description': '形成下降旗形，看跌延续形态'
                    }
        
        return result

    def _check_wedge_patterns(self) -> Dict[str, Dict]:
        """检测楔形形态"""
        result = {}
        highs = self.data['high'].values
        lows = self.data['low'].values
        n = len(highs)
        
        if n >= 20:
            high_slope = np.polyfit(range(20), highs[-20:], 1)[0]
            low_slope = np.polyfit(range(20), lows[-20:], 1)[0]
            
            # 上升楔形
            if high_slope > 0 and low_slope > 0 and high_slope < low_slope:
                result['RISING_WEDGE'] = {
                    'type': 'bearish',
                    'confidence': 0.75,
                    'description': '形成上升楔形，潜在顶部反转信号'
                }
            
            # 下降楔形
            elif high_slope < 0 and low_slope < 0 and high_slope > low_slope:
                result['FALLING_WEDGE'] = {
                    'type': 'bullish',
                    'confidence': 0.75,
                    'description': '形成下降楔形，潜在底部反转信号'
                }
        
        return result
    def get_analysis_report(self) -> str:
        """
        生成分析报告
        :return: 格式化的分析报告字符串
        """
        patterns = self.analyse_all_patterns()
        # 关键形态分析
        bullish_patterns = []
        bearish_patterns = []
        report = []
        report.append("=== 技术分析报告 ===")
        for pattern, details in patterns.items():
            if details['type'] == 'bullish':
                bullish_patterns.append(f"- {pattern}: {details['description']}")
            elif details['type'] == 'bearish':
                bearish_patterns.append(f"- {pattern}: {details['description']}")
            
        if bullish_patterns:
            report.append("\n【主要看涨信号】:")
            report.extend(bullish_patterns)
        
        if bearish_patterns:
            report.append("\n【主要看跌信号】:")
            report.extend(bearish_patterns)
            
        return "\n".join(report)

end_date = datetime.now().strftime("%Y%m%d")
df = ak.stock_zh_a_hist(symbol="600975", period="daily", start_date="20240101", end_date="20241219", adjust="qfq")
df.rename(columns={"日期": "date", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", "成交量": "volume", "成交额": "amount", "振幅": "amplitude", "涨跌幅": "change", "涨跌额": "change_amount", "换手率": "turnover_rate"}, inplace=True)
analyser = PatternAnalyser(df)
patterns = analyser.analyse_all_patterns()
analysis_report = analyser.get_analysis_report()
print(analysis_report)
