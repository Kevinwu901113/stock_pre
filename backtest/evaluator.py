#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测评估模块
提供胜率、平均涨幅、最大回撤、累计收益等指标的计算逻辑
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestEvaluator:
    """
    回测评估器
    提供各种回测性能指标的计算和可视化
    """
    
    def __init__(self, benchmark_data: Optional[pd.DataFrame] = None):
        """
        初始化回测评估器
        
        Args:
            benchmark_data: 基准数据，如沪深300指数，必须包含date和close列
        """
        self.benchmark_data = benchmark_data
    
    def set_benchmark(self, benchmark_data: pd.DataFrame):
        """
        设置基准数据
        
        Args:
            benchmark_data: 基准数据，如沪深300指数，必须包含date和close列
        """
        self.benchmark_data = benchmark_data
    
    def calculate_returns(self, values: pd.DataFrame) -> pd.DataFrame:
        """
        计算收益率序列
        
        Args:
            values: 包含date和total列的DataFrame，表示每日总资产价值
            
        Returns:
            包含date和return列的DataFrame，表示每日收益率
        """
        if values.empty or 'date' not in values.columns or 'total' not in values.columns:
            logger.warning("输入数据格式不正确，无法计算收益率")
            return pd.DataFrame(columns=['date', 'return'])
        
        # 确保日期格式一致
        values = values.copy()
        values['date'] = pd.to_datetime(values['date'])
        values = values.sort_values('date')
        
        # 计算每日收益率
        values['return'] = values['total'].pct_change()
        values['return'] = values['return'].fillna(0)
        
        # 计算累计收益率
        values['cumulative_return'] = (1 + values['return']).cumprod() - 1
        
        return values[['date', 'return', 'cumulative_return']]
    
    def calculate_benchmark_returns(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        计算基准收益率序列
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含date和benchmark_return列的DataFrame
        """
        if self.benchmark_data is None or self.benchmark_data.empty:
            logger.warning("未设置基准数据，无法计算基准收益率")
            return pd.DataFrame(columns=['date', 'benchmark_return', 'benchmark_cumulative_return'])
        
        # 确保日期格式一致
        benchmark = self.benchmark_data.copy()
        benchmark['date'] = pd.to_datetime(benchmark['date'])
        benchmark = benchmark.sort_values('date')
        
        # 过滤日期范围
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        benchmark = benchmark[(benchmark['date'] >= start_date) & (benchmark['date'] <= end_date)]
        
        # 计算每日收益率
        benchmark['benchmark_return'] = benchmark['close'].pct_change()
        benchmark['benchmark_return'] = benchmark['benchmark_return'].fillna(0)
        
        # 计算累计收益率
        benchmark['benchmark_cumulative_return'] = (1 + benchmark['benchmark_return']).cumprod() - 1
        
        return benchmark[['date', 'benchmark_return', 'benchmark_cumulative_return']]
    
    def calculate_win_rate(self, trades: pd.DataFrame) -> float:
        """
        计算胜率
        
        Args:
            trades: 交易记录DataFrame，必须包含action和profit列
            
        Returns:
            胜率（0-1之间的浮点数）
        """
        if trades.empty or 'action' not in trades.columns or 'profit' not in trades.columns:
            logger.warning("交易记录格式不正确，无法计算胜率")
            return 0.0
        
        # 筛选卖出交易
        sell_trades = trades[trades['action'] == 'sell']
        if sell_trades.empty:
            return 0.0
        
        # 计算盈利交易数量
        winning_trades = sell_trades[sell_trades['profit'] > 0]
        win_rate = len(winning_trades) / len(sell_trades)
        
        return win_rate
    
    def calculate_average_return(self, trades: pd.DataFrame) -> float:
        """
        计算平均收益率
        
        Args:
            trades: 交易记录DataFrame，必须包含action和profit_rate列
            
        Returns:
            平均收益率
        """
        if trades.empty or 'action' not in trades.columns or 'profit_rate' not in trades.columns:
            logger.warning("交易记录格式不正确，无法计算平均收益率")
            return 0.0
        
        # 筛选卖出交易
        sell_trades = trades[trades['action'] == 'sell']
        if sell_trades.empty:
            return 0.0
        
        # 计算平均收益率
        avg_return = sell_trades['profit_rate'].mean()
        
        return avg_return
    
    def calculate_max_drawdown(self, values: pd.DataFrame) -> float:
        """
        计算最大回撤
        
        Args:
            values: 包含date和total列的DataFrame，表示每日总资产价值
            
        Returns:
            最大回撤（0-1之间的浮点数）
        """
        if values.empty or 'total' not in values.columns:
            logger.warning("输入数据格式不正确，无法计算最大回撤")
            return 0.0
        
        # 计算最大回撤
        values = values.sort_values('date')
        total_values = values['total'].values
        
        # 计算累计最大值
        max_so_far = np.maximum.accumulate(total_values)
        # 计算相对回撤
        drawdown = 1 - total_values / max_so_far
        # 最大回撤
        max_drawdown = np.max(drawdown)
        
        return max_drawdown
    
    def calculate_sharpe_ratio(self, returns: pd.DataFrame, risk_free_rate: float = 0.03, periods_per_year: int = 252) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 包含return列的DataFrame，表示每日收益率
            risk_free_rate: 无风险利率，默认为3%
            periods_per_year: 一年的交易周期数，日线数据为252
            
        Returns:
            夏普比率
        """
        if returns.empty or 'return' not in returns.columns:
            logger.warning("输入数据格式不正确，无法计算夏普比率")
            return 0.0
        
        # 计算每日超额收益率
        daily_risk_free = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        excess_returns = returns['return'] - daily_risk_free
        
        # 计算夏普比率
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year)
        
        return sharpe_ratio
    
    def calculate_sortino_ratio(self, returns: pd.DataFrame, risk_free_rate: float = 0.03, periods_per_year: int = 252) -> float:
        """
        计算索提诺比率（只考虑下行风险）
        
        Args:
            returns: 包含return列的DataFrame，表示每日收益率
            risk_free_rate: 无风险利率，默认为3%
            periods_per_year: 一年的交易周期数，日线数据为252
            
        Returns:
            索提诺比率
        """
        if returns.empty or 'return' not in returns.columns:
            logger.warning("输入数据格式不正确，无法计算索提诺比率")
            return 0.0
        
        # 计算每日超额收益率
        daily_risk_free = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        excess_returns = returns['return'] - daily_risk_free
        
        # 计算下行风险（只考虑负收益）
        negative_returns = excess_returns[excess_returns < 0]
        if len(negative_returns) == 0 or negative_returns.std() == 0:
            return 0.0
        
        downside_risk = negative_returns.std() * np.sqrt(periods_per_year)
        
        # 计算索提诺比率
        sortino_ratio = excess_returns.mean() * periods_per_year / downside_risk
        
        return sortino_ratio
    
    def calculate_calmar_ratio(self, values: pd.DataFrame, periods_per_year: int = 252) -> float:
        """
        计算卡玛比率（年化收益率除以最大回撤）
        
        Args:
            values: 包含date和total列的DataFrame，表示每日总资产价值
            periods_per_year: 一年的交易周期数，日线数据为252
            
        Returns:
            卡玛比率
        """
        if values.empty or 'date' not in values.columns or 'total' not in values.columns:
            logger.warning("输入数据格式不正确，无法计算卡玛比率")
            return 0.0
        
        # 计算年化收益率
        values = values.sort_values('date')
        start_value = values['total'].iloc[0]
        end_value = values['total'].iloc[-1]
        days = (values['date'].iloc[-1] - values['date'].iloc[0]).days
        years = days / 365
        
        if years == 0 or start_value == 0:
            return 0.0
        
        annualized_return = (end_value / start_value) ** (1 / years) - 1
        
        # 计算最大回撤
        max_drawdown = self.calculate_max_drawdown(values)
        
        # 计算卡玛比率
        if max_drawdown == 0:
            return 0.0
        
        calmar_ratio = annualized_return / max_drawdown
        
        return calmar_ratio
    
    def calculate_alpha_beta(self, returns: pd.DataFrame, benchmark_returns: pd.DataFrame, risk_free_rate: float = 0.03) -> Tuple[float, float]:
        """
        计算阿尔法和贝塔系数
        
        Args:
            returns: 包含return列的DataFrame，表示策略每日收益率
            benchmark_returns: 包含benchmark_return列的DataFrame，表示基准每日收益率
            risk_free_rate: 无风险利率，默认为3%
            
        Returns:
            (alpha, beta) 元组
        """
        if returns.empty or benchmark_returns.empty:
            logger.warning("输入数据为空，无法计算阿尔法和贝塔")
            return 0.0, 0.0
        
        # 合并数据
        merged = pd.merge(returns, benchmark_returns, on='date')
        if merged.empty:
            logger.warning("策略收益率和基准收益率没有重叠的日期，无法计算阿尔法和贝塔")
            return 0.0, 0.0
        
        # 计算每日超额收益率
        daily_risk_free = (1 + risk_free_rate) ** (1 / 252) - 1
        merged['excess_return'] = merged['return'] - daily_risk_free
        merged['excess_benchmark_return'] = merged['benchmark_return'] - daily_risk_free
        
        # 计算贝塔系数（策略相对于基准的波动率）
        covariance = merged['excess_return'].cov(merged['excess_benchmark_return'])
        benchmark_variance = merged['excess_benchmark_return'].var()
        
        if benchmark_variance == 0:
            beta = 0.0
        else:
            beta = covariance / benchmark_variance
        
        # 计算阿尔法（超额收益率）
        alpha = merged['excess_return'].mean() * 252 - beta * merged['excess_benchmark_return'].mean() * 252
        
        return alpha, beta
    
    def calculate_information_ratio(self, returns: pd.DataFrame, benchmark_returns: pd.DataFrame) -> float:
        """
        计算信息比率
        
        Args:
            returns: 包含return列的DataFrame，表示策略每日收益率
            benchmark_returns: 包含benchmark_return列的DataFrame，表示基准每日收益率
            
        Returns:
            信息比率
        """
        if returns.empty or benchmark_returns.empty:
            logger.warning("输入数据为空，无法计算信息比率")
            return 0.0
        
        # 合并数据
        merged = pd.merge(returns, benchmark_returns, on='date')
        if merged.empty:
            logger.warning("策略收益率和基准收益率没有重叠的日期，无法计算信息比率")
            return 0.0
        
        # 计算超额收益率
        merged['active_return'] = merged['return'] - merged['benchmark_return']
        
        # 计算信息比率
        if merged['active_return'].std() == 0:
            return 0.0
        
        information_ratio = merged['active_return'].mean() / merged['active_return'].std() * np.sqrt(252)
        
        return information_ratio
    
    def evaluate(self, backtest_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估回测结果，计算各项指标
        
        Args:
            backtest_result: 回测结果字典，包含trades、daily_values、daily_returns等键
            
        Returns:
            评估指标字典
        """
        # 提取回测数据
        trades = backtest_result.get('trades', pd.DataFrame())
        daily_values = backtest_result.get('daily_values', pd.DataFrame())
        daily_returns = backtest_result.get('daily_returns', pd.DataFrame())
        
        # 计算收益率序列（如果未提供）
        if daily_returns.empty and not daily_values.empty:
            daily_returns = self.calculate_returns(daily_values)
        
        # 计算基准收益率（如果有基准数据）
        benchmark_returns = pd.DataFrame()
        if self.benchmark_data is not None and not daily_values.empty:
            start_date = daily_values['date'].min()
            end_date = daily_values['date'].max()
            benchmark_returns = self.calculate_benchmark_returns(start_date, end_date)
        
        # 计算各项指标
        evaluation = {}
        
        # 基础指标
        if not daily_values.empty:
            # 总收益率
            initial_value = daily_values['total'].iloc[0]
            final_value = daily_values['total'].iloc[-1]
            total_return = (final_value - initial_value) / initial_value
            evaluation['total_return'] = total_return
            
            # 年化收益率
            days = (pd.to_datetime(daily_values['date'].iloc[-1]) - 
                    pd.to_datetime(daily_values['date'].iloc[0])).days
            years = days / 365
            if years > 0:
                annualized_return = (1 + total_return) ** (1 / years) - 1
                evaluation['annualized_return'] = annualized_return
            else:
                evaluation['annualized_return'] = 0.0
            
            # 最大回撤
            max_drawdown = self.calculate_max_drawdown(daily_values)
            evaluation['max_drawdown'] = max_drawdown
            
            # 卡玛比率
            if max_drawdown > 0:
                evaluation['calmar_ratio'] = evaluation['annualized_return'] / max_drawdown
            else:
                evaluation['calmar_ratio'] = 0.0
        
        # 交易指标
        if not trades.empty:
            # 胜率
            win_rate = self.calculate_win_rate(trades)
            evaluation['win_rate'] = win_rate
            
            # 平均收益率
            avg_return = self.calculate_average_return(trades)
            evaluation['avg_return'] = avg_return
            
            # 交易次数
            trade_count = len(trades[trades['action'] == 'sell'])
            evaluation['trade_count'] = trade_count
        
        # 风险调整指标
        if not daily_returns.empty:
            # 夏普比率
            sharpe_ratio = self.calculate_sharpe_ratio(daily_returns)
            evaluation['sharpe_ratio'] = sharpe_ratio
            
            # 索提诺比率
            sortino_ratio = self.calculate_sortino_ratio(daily_returns)
            evaluation['sortino_ratio'] = sortino_ratio
        
        # 相对基准指标
        if not daily_returns.empty and not benchmark_returns.empty:
            # 阿尔法和贝塔
            alpha, beta = self.calculate_alpha_beta(daily_returns, benchmark_returns)
            evaluation['alpha'] = alpha
            evaluation['beta'] = beta
            
            # 信息比率
            information_ratio = self.calculate_information_ratio(daily_returns, benchmark_returns)
            evaluation['information_ratio'] = information_ratio
        
        return evaluation
    
    def plot_equity_curve(self, daily_values: pd.DataFrame, benchmark_returns: Optional[pd.DataFrame] = None, 
                         save_path: Optional[str] = None, show_plot: bool = True):
        """
        绘制权益曲线
        
        Args:
            daily_values: 包含date和total列的DataFrame，表示每日总资产价值
            benchmark_returns: 包含date和benchmark_cumulative_return列的DataFrame，表示基准累计收益率
            save_path: 图表保存路径，如果为None则不保存
            show_plot: 是否显示图表
        """
        if daily_values.empty or 'date' not in daily_values.columns or 'total' not in daily_values.columns:
            logger.warning("输入数据格式不正确，无法绘制权益曲线")
            return
        
        # 计算策略累计收益率
        daily_values = daily_values.copy()
        daily_values['date'] = pd.to_datetime(daily_values['date'])
        daily_values = daily_values.sort_values('date')
        initial_value = daily_values['total'].iloc[0]
        daily_values['strategy_cumulative_return'] = daily_values['total'] / initial_value - 1
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 绘制策略曲线
        plt.plot(daily_values['date'], daily_values['strategy_cumulative_return'], label='策略收益率', linewidth=2)
        
        # 绘制基准曲线（如果有）
        if benchmark_returns is not None and not benchmark_returns.empty:
            benchmark_returns = benchmark_returns.copy()
            benchmark_returns['date'] = pd.to_datetime(benchmark_returns['date'])
            merged = pd.merge(daily_values[['date']], benchmark_returns, on='date', how='left')
            if 'benchmark_cumulative_return' in merged.columns:
                plt.plot(merged['date'], merged['benchmark_cumulative_return'], label='基准收益率', linewidth=2, linestyle='--')
        
        # 设置图表属性
        plt.title('策略累计收益率曲线', fontsize=14)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('累计收益率', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(fontsize=12)
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"权益曲线已保存至 {save_path}")
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_drawdown_curve(self, daily_values: pd.DataFrame, save_path: Optional[str] = None, show_plot: bool = True):
        """
        绘制回撤曲线
        
        Args:
            daily_values: 包含date和total列的DataFrame，表示每日总资产价值
            save_path: 图表保存路径，如果为None则不保存
            show_plot: 是否显示图表
        """
        if daily_values.empty or 'date' not in daily_values.columns or 'total' not in daily_values.columns:
            logger.warning("输入数据格式不正确，无法绘制回撤曲线")
            return
        
        # 计算回撤序列
        daily_values = daily_values.copy()
        daily_values['date'] = pd.to_datetime(daily_values['date'])
        daily_values = daily_values.sort_values('date')
        
        # 计算累计最大值
        daily_values['peak'] = daily_values['total'].cummax()
        # 计算回撤
        daily_values['drawdown'] = (daily_values['peak'] - daily_values['total']) / daily_values['peak']
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 绘制回撤曲线
        plt.plot(daily_values['date'], daily_values['drawdown'], label='回撤', linewidth=2, color='red')
        
        # 设置图表属性
        plt.title('策略回撤曲线', fontsize=14)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('回撤', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.fill_between(daily_values['date'], 0, daily_values['drawdown'], color='red', alpha=0.3)
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"回撤曲线已保存至 {save_path}")
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def generate_report(self, backtest_result: Dict[str, Any], output_dir: str = './reports', 
                       report_name: Optional[str] = None, save_plots: bool = True):
        """
        生成回测报告
        
        Args:
            backtest_result: 回测结果字典
            output_dir: 报告输出目录
            report_name: 报告名称，如果为None则使用当前时间戳
            save_plots: 是否保存图表
        
        Returns:
            报告文件路径
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成报告名称
        if report_name is None:
            report_name = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 评估回测结果
        evaluation = self.evaluate(backtest_result)
        
        # 提取回测数据
        trades = backtest_result.get('trades', pd.DataFrame())
        daily_values = backtest_result.get('daily_values', pd.DataFrame())
        
        # 计算基准收益率（如果有基准数据）
        benchmark_returns = pd.DataFrame()
        if self.benchmark_data is not None and not daily_values.empty:
            start_date = daily_values['date'].min()
            end_date = daily_values['date'].max()
            benchmark_returns = self.calculate_benchmark_returns(start_date, end_date)
        
        # 生成报告内容
        report_content = []
        report_content.append(f"# 回测报告: {report_name}\n")
        report_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 回测参数
        report_content.append("## 回测参数\n")
        if not daily_values.empty:
            start_date = pd.to_datetime(daily_values['date'].min()).strftime('%Y-%m-%d')
            end_date = pd.to_datetime(daily_values['date'].max()).strftime('%Y-%m-%d')
            report_content.append(f"- 回测区间: {start_date} 至 {end_date}\n")
        
        # 回测结果摘要
        report_content.append("## 回测结果摘要\n")
        report_content.append("| 指标 | 数值 |\n")
        report_content.append("| --- | --- |\n")
        
        # 格式化评估指标
        for key, value in evaluation.items():
            if key in ['total_return', 'annualized_return', 'max_drawdown', 'win_rate', 'avg_return']:
                formatted_value = f"{value:.2%}"
            elif key in ['trade_count']:
                formatted_value = f"{int(value)}"
            else:
                formatted_value = f"{value:.4f}"
            
            # 翻译指标名称
            indicator_names = {
                'total_return': '总收益率',
                'annualized_return': '年化收益率',
                'max_drawdown': '最大回撤',
                'calmar_ratio': '卡玛比率',
                'win_rate': '胜率',
                'avg_return': '平均收益率',
                'trade_count': '交易次数',
                'sharpe_ratio': '夏普比率',
                'sortino_ratio': '索提诺比率',
                'alpha': '阿尔法',
                'beta': '贝塔',
                'information_ratio': '信息比率'
            }
            
            indicator_name = indicator_names.get(key, key)
            report_content.append(f"| {indicator_name} | {formatted_value} |\n")
        
        # 保存图表
        if save_plots and not daily_values.empty:
            # 权益曲线
            equity_curve_path = os.path.join(output_dir, f"{report_name}_equity_curve.png")
            self.plot_equity_curve(daily_values, benchmark_returns, equity_curve_path, show_plot=False)
            report_content.append("\n## 权益曲线\n")
            report_content.append(f"![权益曲线]({equity_curve_path})\n")
            
            # 回撤曲线
            drawdown_curve_path = os.path.join(output_dir, f"{report_name}_drawdown_curve.png")
            self.plot_drawdown_curve(daily_values, drawdown_curve_path, show_plot=False)
            report_content.append("\n## 回撤曲线\n")
            report_content.append(f"![回撤曲线]({drawdown_curve_path})\n")
        
        # 交易明细
        if not trades.empty and len(trades) > 0:
            report_content.append("\n## 交易明细\n")
            
            # 筛选卖出交易并按收益率排序
            sell_trades = trades[trades['action'] == 'sell'].copy()
            if not sell_trades.empty:
                sell_trades = sell_trades.sort_values('profit_rate', ascending=False)
                
                # 取前10笔最盈利和最亏损的交易
                top_trades = sell_trades.head(10)
                bottom_trades = sell_trades.tail(10)
                
                # 最盈利交易
                report_content.append("### 最盈利交易 (Top 10)\n")
                report_content.append("| 日期 | 股票代码 | 买入价 | 卖出价 | 收益率 |\n")
                report_content.append("| --- | --- | --- | --- | --- |\n")
                
                for _, trade in top_trades.iterrows():
                    symbol = trade['symbol']
                    date = pd.to_datetime(trade['date']).strftime('%Y-%m-%d')
                    
                    # 查找对应的买入交易
                    buy_trade = trades[(trades['symbol'] == symbol) & 
                                      (trades['action'] == 'buy') & 
                                      (pd.to_datetime(trades['date']) < pd.to_datetime(trade['date']))].iloc[-1]
                    
                    buy_price = buy_trade['price']
                    sell_price = trade['price']
                    profit_rate = trade['profit_rate']
                    
                    report_content.append(f"| {date} | {symbol} | {buy_price:.2f} | {sell_price:.2f} | {profit_rate:.2%} |\n")
                
                # 最亏损交易
                report_content.append("\n### 最亏损交易 (Bottom 10)\n")
                report_content.append("| 日期 | 股票代码 | 买入价 | 卖出价 | 收益率 |\n")
                report_content.append("| --- | --- | --- | --- | --- |\n")
                
                for _, trade in bottom_trades.iterrows():
                    symbol = trade['symbol']
                    date = pd.to_datetime(trade['date']).strftime('%Y-%m-%d')
                    
                    # 查找对应的买入交易
                    buy_trade = trades[(trades['symbol'] == symbol) & 
                                      (trades['action'] == 'buy') & 
                                      (pd.to_datetime(trades['date']) < pd.to_datetime(trade['date']))].iloc[-1]
                    
                    buy_price = buy_trade['price']
                    sell_price = trade['price']
                    profit_rate = trade['profit_rate']
                    
                    report_content.append(f"| {date} | {symbol} | {buy_price:.2f} | {sell_price:.2f} | {profit_rate:.2%} |\n")
        
        # 写入报告文件
        report_file = os.path.join(output_dir, f"{report_name}.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.writelines(report_content)
        
        logger.info(f"回测报告已生成: {report_file}")
        return report_file