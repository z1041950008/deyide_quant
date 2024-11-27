import pandas as pd
import json
import numpy as np
import os

class Backtest:
    def __init__(self, strategy, initial_capital=1000000, position_size=0.1, benchmark_code='000300.SH'):
        """
        回测框架初始化
        Args:
            strategy: 交易策略类实例
            initial_capital: 初始资金
            position_size: 每个持仓的资金比例
            benchmark_code: 基准指数代码，默认沪深300
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.benchmark_code = benchmark_code
        
    def run(self, start_date: str, end_date: str) -> tuple:
        """
        运行回测
        Args:
            start_date: 回测开始日期 'YYYY-MM-DD'
            end_date: 回测结束日期 'YYYY-MM-DD'
        Returns:
            tuple: (回测记录, 交易记录列表)
        """
        print(f"开始回测 {start_date} 至 {end_date}")
        # 创建回测记录
        backtest_record = {
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": self.initial_capital,
            "final_capital": self.initial_capital,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
        }
        
        current_positions = {}
        trade_records = []
        daily_capitals = [self.initial_capital]
        daily_positions = [0]
        current_capital = self.initial_capital
        max_position = 0
        
        trading_dates = pd.date_range(start=start_date, end=end_date, freq='B')
        try:
            
            for date in trading_dates:
                date_str = date.strftime('%Y-%m-%d')
                # 调用策略获取交易信号
                buy_signals, sell_signals, stock_list = self.strategy.run(date_str)
                
                # 记录当前持仓数量
                current_position_count = len(current_positions)
                daily_positions.append(current_position_count)
                max_position = max(max_position, current_position_count)
                
                # 处理卖出信号
                for signal in sell_signals:
                    if signal['code'] in current_positions:
                            close_price = signal['close_price']  
                            position = current_positions[signal['code']]
                            profit = (close_price - position['entry_price']) * position['shares']
                            current_capital += position['shares'] * close_price
                            
                            trade_record = {
                                'trade_date': date_str,
                                'stock_code': signal['code'],
                                'stock_name': signal['name'],
                                'action': 'SELL',
                                'price': close_price,
                                'shares': position['shares'],
                                'profit': profit,
                                'capital_after_trade': current_capital
                            }
                            trade_records.append(trade_record)
                            
                            if profit > 0:
                                backtest_record['winning_trades'] += 1
                            else:
                                backtest_record['losing_trades'] += 1
                            
                            del current_positions[signal['code']]
                
                # 处理买入信号
                available_capital = current_capital * self.position_size
                for signal in buy_signals:
                    # 从 stock_list 中获取价格信息
                    if signal['code'] not in current_positions and available_capital > 0:
                        close_price = signal['close_price']  
                        shares = int(available_capital / close_price)
                        if shares > 0:
                            cost = shares * close_price
                            current_capital -= cost
                            
                            current_positions[signal['code']] = {
                                'entry_price': close_price,
                                'shares': shares,
                                'entry_date': date_str
                            }
                            
                            trade_record = {
                                'trade_date': date_str,
                                'stock_code': signal['code'],
                                'stock_name': signal['name'],
                                'action': 'BUY',
                                'price': close_price,
                                'shares': shares,
                                'profit': 0,
                                'capital_after_trade': current_capital
                            }
                            trade_records.append(trade_record)
                
                for key in current_positions.keys():
                    current_positions[key]['current_price'] = [stock['latest_price'] for stock in stock_list if stock['代码'] == key][0]
                # 计算最终统计数据
                # 计算当前持仓市值
                positions_value = sum(
                    current_positions[key]['shares'] * current_positions[key]['current_price']
                    for key in current_positions.keys()
                )
                daily_capitals.append(current_capital + positions_value)
                backtest_record['total_trades'] = len(trade_records)
            
            final_capital = daily_capitals[-1]
            backtest_record['final_capital'] = final_capital
            
            total_trades = backtest_record['winning_trades'] + backtest_record['losing_trades']
            backtest_record['win_rate'] = (backtest_record['winning_trades'] / total_trades) if total_trades > 0 else 0
            
            # 计算持仓周期统计
            holding_periods = []
            for record in trade_records:
                if record['action'] == 'SELL':
                    entry_date = None
                    # 查找对应的买入记录
                    for prev_record in trade_records:
                        if (prev_record['action'] == 'BUY' and 
                            prev_record['stock_code'] == record['stock_code'] and 
                            prev_record['trade_date'] < record['trade_date']):
                            entry_date = pd.to_datetime(prev_record['trade_date'])
                            break
                    if entry_date:
                        exit_date = pd.to_datetime(record['trade_date'])
                        holding_period = (exit_date - entry_date).days
                        holding_periods.append(holding_period)
            
            backtest_record['avg_holding_period'] = sum(holding_periods) / len(holding_periods) if holding_periods else 0
            backtest_record['max_holding_period'] = max(holding_periods) if holding_periods else 0
            
            # 计算收益率指标
            total_return = (final_capital - self.initial_capital) / self.initial_capital
            days = len(trading_dates)
            annual_return = (1 + total_return) ** (252 / days) - 1
            
            # 计算波动率
            daily_returns = [(c - p) / p for c, p in zip(daily_capitals[1:], daily_capitals[:-1])]
            volatility = pd.Series(daily_returns).std() * (252 ** 0.5)  # 年化波动率
            
            backtest_record['total_return'] = total_return
            backtest_record['annual_return'] = annual_return
            backtest_record['volatility'] = volatility
            
            # 计算夏普比率 (假设无风险利率为3%)
            risk_free_rate = 0.03
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility != 0 else 0
            backtest_record['sharpe_ratio'] = sharpe_ratio
            
            # 计算最大回撤
            peak = daily_capitals[0]
            max_drawdown = 0
            for capital in daily_capitals:
                if capital > peak:
                    peak = capital
                drawdown = (peak - capital) / peak
                max_drawdown = max(max_drawdown, drawdown)
            backtest_record['max_drawdown'] = max_drawdown
            
            # 计算胜率
            total_trades = backtest_record['winning_trades'] + backtest_record['losing_trades']
            backtest_record['win_rate'] = (backtest_record['winning_trades'] / total_trades) if total_trades > 0 else 0
            
            # 计算平均持仓数量
            backtest_record['avg_position'] = sum(daily_positions) / len(daily_positions)
            backtest_record['max_position'] = max_position
            
            # 生成收益率曲线数据
            return_curve = []
            for i, capital in enumerate(daily_capitals):
                return_rate = (capital - self.initial_capital) / self.initial_capital
                date = trading_dates[i] if i < len(trading_dates) else trading_dates[-1]
                return_curve.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'return_rate': return_rate
                })
            
            # 将收益率曲线转换为JSON字符串存储
            backtest_record['return_curve'] = json.dumps(return_curve)
            
            
            # 计算总收益和总盈利
            total_return = (final_capital - self.initial_capital) / self.initial_capital
            total_profit = final_capital - self.initial_capital
            backtest_record['total_profit'] = total_profit
            
            # 在return之前添加生成HTML报告的代码
            self.generate_html_report(backtest_record, trade_records, start_date, end_date)
            
        except Exception as e:
            print(f"回测过程中出错: {str(e)}")
            raise
            
        return backtest_record, trade_records
    
    def generate_html_report(self, backtest_record: dict, trade_records: list, start_date: str, end_date: str):
        """生成HTML回测报告"""
        # 解析收益率曲线数据
        return_curve_data = json.loads(backtest_record['return_curve'])
        dates = [item['date'] for item in return_curve_data]
        returns = [item['return_rate'] * 100 for item in return_curve_data]  # 转换为百分比
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>回测报告 ({start_date} 至 {end_date})</title>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f5f5f5; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
                h2 {{ color: #333; }}
                #return-curve {{ width: 100%; height: 400px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>回测报告</h1>
                
                <div class="section">
                    <h2>收益率曲线</h2>
                    <div id="return-curve"></div>
                </div>
                
                <div class="summary">
                    <h2>回测概况</h2>
                    <table>
                        <tr><td>回测期间</td><td>{start_date} 至 {end_date}</td></tr>
                        <tr><td>初始资金</td><td>{backtest_record['initial_capital']:,.2f}</td></tr>
                        <tr><td>最终资金</td><td>{backtest_record['final_capital']:,.2f}</td></tr>
                        <tr><td>总收益率</td><td>{backtest_record['total_return']:.2%}</td></tr>
                        <tr><td>年化收益率</td><td>{backtest_record['annual_return']:.2%}</td></tr>
                        <tr><td>夏普比率</td><td>{backtest_record['sharpe_ratio']:.2f}</td></tr>
                        <tr><td>最大回撤</td><td>{backtest_record['max_drawdown']:.2%}</td></tr>
                        <tr><td>波动率</td><td>{backtest_record['volatility']:.2%}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>交易统计</h2>
                    <table>
                        <tr><td>总交易次数</td><td>{backtest_record['total_trades']}</td></tr>
                        <tr><td>盈利交易次数</td><td>{backtest_record['winning_trades']}</td></tr>
                        <tr><td>亏损交易次数</td><td>{backtest_record['losing_trades']}</td></tr>
                        <tr><td>胜率</td><td>{backtest_record['win_rate']:.2%}</td></tr>
                        <tr><td>平均持仓周期</td><td>{backtest_record['avg_holding_period']:.1f}天</td></tr>
                        <tr><td>最长持仓周期</td><td>{backtest_record['max_holding_period']}天</td></tr>
                        <tr><td>平均持仓数量</td><td>{backtest_record['avg_position']:.1f}</td></tr>
                        <tr><td>最大持仓数量</td><td>{backtest_record['max_position']}</td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>交易记录</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>日期</th>
                                <th>股票代码</th>
                                <th>股票名称</th>
                                <th>操作</th>
                                <th>价格</th>
                                <th>数量</th>
                                <th>盈亏</th>
                            </tr>
                        </thead>
                        <tbody>
"""

        # 分开处理交易记录
        for record in trade_records:
            html_content += f"""
                            <tr>
                                <td>{record['trade_date']}</td>
                                <td>{record['stock_code']}</td>
                                <td>{record['stock_name']}</td>
                                <td>{record['action']}</td>
                                <td>{record['price']:.2f}</td>
                                <td>{record['shares']}</td>
                                <td>{record['profit']:.2f}</td>
                            </tr>
"""

        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <script>
                // 初始化收益率曲线图表
                var chartDom = document.getElementById('return-curve');
                var myChart = echarts.init(chartDom);
        """ 
        html_content += f""" var dates = {dates}; """
        html_content += f""" var returns = {returns}; """
        html_content += """
                var option = {
                    title: {        
                        text: '策略收益率曲线',
                        left: 'center'
                    },
                    tooltip: {
                        trigger: 'axis',
                        formatter: function(params) {
                            return params[0].name + '<br/>' +
                                   params[0].seriesName + ': ' + params[0].value.toFixed(2) + '%';
                        }
                    },
                    xAxis: {
                        type: 'category',
                        data: dates,
                        axisLabel: {
                            rotate: 45
                        }
                    },
                    yAxis: {
                        type: 'value',
                        name: '收益率(%)',
                        axisLabel: {
                            formatter: '{value}%'
                        }
                    },
                    series: [
                        {
                            name: '收益率',
                            type: 'line',
                            data: returns,
                            smooth: true,
                            lineStyle: {
                                width: 2
                            },
                            areaStyle: {
                                opacity: 0.2
                            }
                        }
                    ],
                    grid: {
                        left: '3%',
                        right: '4%',
                        bottom: '15%',
                        containLabel: true
                    }
                };
                myChart.setOption(option);
                
                // 响应窗口大小变化
                window.addEventListener('resize', function() {  
                    myChart.resize();
                });
            </script>
        </body>
        </html>
        """
        
        # 确保html目录存在
        os.makedirs('html', exist_ok=True)
        
        # 生成带序号的文件名
        base_filename = f'backtest_report_{start_date}_{end_date}'
        counter = 1
        while os.path.exists(f'html/{base_filename}_{counter}.html'):
            counter += 1
        filename = f'{base_filename}_{counter}.html'
        
        # 生成HTML文件
        with open(f'html/{filename}', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML报告已生成: html/{filename}")

