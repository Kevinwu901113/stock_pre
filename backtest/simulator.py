#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测模拟器模块
实现历史模拟 T 日尾盘买入、T+1 日开盘/均价卖出的回测流程
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import logging
from datetime import datetime, timedelta
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestSimulator:
    """
    回测模拟器
    实现 T 日尾盘买入、T+1 日开盘/均价卖出的回测流程
    """
    
    def __init__(self, 
                 start_date: str = None, 
                 end_date: str = None,
                 initial_capital: float = 1000000.0,
                 commission_rate: float = 0.0003,
                 slippage: float = 0.0001,
                 max_position_per_stock: float = 0.1,
                 max_stocks_per_day: int = 5):
        """
        初始化回测模拟器
        
        Args:
            start_date: 回测开始日期，格式为'YYYY-MM-DD'
            end_date: 回测结束日期，格式为'YYYY-MM-DD'
            initial_capital: 初始资金
            commission_rate: 交易佣金率
            slippage: 滑点率
            max_position_per_stock: 单只股票最大仓位比例
            max_stocks_per_day: 每日最大买入股票数量
        """
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.max_position_per_stock = max_position_per_stock
        self.max_stocks_per_day = max_stocks_per_day
        
        # 回测结果
        self.positions = {}  # 当前持仓 {symbol: {amount: 数量, cost: 成本}}
        self.trade_history = []  # 交易记录
        self.daily_returns = []  # 每日收益率
        self.daily_values = []  # 每日总资产
        self.daily_cash = []  # 每日现金
        
        # 回测状态
        self.current_date = None
        self.trading_dates = []
        self.stock_data = {}
    
    def load_data(self, stock_data: Dict[str, pd.DataFrame]):
        """
        加载股票数据
        
        Args:
            stock_data: 股票数据字典，格式为 {symbol: dataframe}
                        dataframe 必须包含 date, open, high, low, close, volume 列
        """
        self.stock_data = stock_data
        
        # 提取交易日期
        all_dates = set()
        for symbol, df in stock_data.items():
            if 'date' in df.columns:
                dates = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d').tolist()
                all_dates.update(dates)
        
        self.trading_dates = sorted(list(all_dates))
        
        # 如果未指定开始和结束日期，则使用数据中的第一天和最后一天
        if self.start_date is None:
            self.start_date = self.trading_dates[0]
        if self.end_date is None:
            self.end_date = self.trading_dates[-1]
            
        # 过滤交易日期
        self.trading_dates = [d for d in self.trading_dates 
                             if self.start_date <= d <= self.end_date]
        
        logger.info(f"加载了{len(stock_data)}只股票的数据，交易日期范围：{self.start_date}至{self.end_date}")
    
    def get_next_trading_day(self, date: str) -> str:
        """
        获取下一个交易日
        
        Args:
            date: 当前日期
            
        Returns:
            下一个交易日，如果没有下一个交易日则返回None
        """
        try:
            idx = self.trading_dates.index(date)
            if idx < len(self.trading_dates) - 1:
                return self.trading_dates[idx + 1]
        except ValueError:
            pass
        return None
    
    def execute_buy(self, date: str, recommendations: pd.DataFrame):
        """
        执行买入操作
        
        Args:
            date: 交易日期
            recommendations: 推荐股票DataFrame，必须包含symbol和score列
        """
        if date not in self.trading_dates:
            logger.warning(f"{date}不是交易日，无法执行买入操作")
            return
        
        # 按评分排序并限制买入数量
        if 'score' in recommendations.columns:
            recommendations = recommendations.sort_values('score', ascending=False)
        
        # 限制买入数量
        recommendations = recommendations.head(self.max_stocks_per_day)
        
        # 计算每只股票的买入资金
        available_capital = self.current_capital
        capital_per_stock = min(
            available_capital * self.max_position_per_stock,
            available_capital / len(recommendations) if len(recommendations) > 0 else 0
        )
        
        for _, row in recommendations.iterrows():
            symbol = row['symbol']
            
            # 检查股票数据是否存在
            if symbol not in self.stock_data:
                logger.warning(f"股票{symbol}数据不存在，跳过买入")
                continue
            
            # 获取股票当日数据
            stock_df = self.stock_data[symbol]
            stock_df['date'] = pd.to_datetime(stock_df['date']).dt.strftime('%Y-%m-%d')
            day_data = stock_df[stock_df['date'] == date]
            
            if day_data.empty:
                logger.warning(f"股票{symbol}在{date}没有数据，跳过买入")
                continue
            
            # 使用收盘价买入
            price = day_data['close'].values[0]
            
            # 考虑滑点
            buy_price = price * (1 + self.slippage)
            
            # 计算可买入数量（取整百）
            shares = int((capital_per_stock / buy_price) / 100) * 100
            if shares <= 0:
                continue
            
            # 计算实际买入金额
            cost = shares * buy_price
            commission = cost * self.commission_rate
            total_cost = cost + commission
            
            # 检查资金是否足够
            if total_cost > available_capital:
                shares = int((available_capital / (buy_price * (1 + self.commission_rate))) / 100) * 100
                if shares <= 0:
                    continue
                cost = shares * buy_price
                commission = cost * self.commission_rate
                total_cost = cost + commission
            
            # 更新资金和持仓
            self.current_capital -= total_cost
            available_capital -= total_cost
            
            # 更新持仓
            if symbol in self.positions:
                # 已有持仓，更新平均成本
                old_amount = self.positions[symbol]['amount']
                old_cost = self.positions[symbol]['cost']
                new_amount = old_amount + shares
                new_cost = old_cost + cost
                self.positions[symbol] = {
                    'amount': new_amount,
                    'cost': new_cost,
                    'buy_date': date
                }
            else:
                # 新建持仓
                self.positions[symbol] = {
                    'amount': shares,
                    'cost': cost,
                    'buy_date': date
                }
            
            # 记录交易
            self.trade_history.append({
                'date': date,
                'symbol': symbol,
                'action': 'buy',
                'price': buy_price,
                'shares': shares,
                'cost': cost,
                'commission': commission,
                'total_cost': total_cost
            })
            
            logger.info(f"{date} 买入 {symbol}: {shares}股，价格{buy_price:.2f}，总成本{total_cost:.2f}")
    
    def execute_sell(self, date: str, sell_type: str = 'open'):
        """
        执行卖出操作
        
        Args:
            date: 交易日期
            sell_type: 卖出类型，'open'表示开盘价卖出，'vwap'表示成交量加权平均价卖出
        """
        if date not in self.trading_dates:
            logger.warning(f"{date}不是交易日，无法执行卖出操作")
            return
        
        # 遍历当前持仓
        symbols_to_remove = []
        for symbol, position in self.positions.items():
            # 检查是否是T+1日
            buy_date = position['buy_date']
            next_trading_day = self.get_next_trading_day(buy_date)
            if next_trading_day != date:
                continue
            
            # 获取股票当日数据
            if symbol not in self.stock_data:
                logger.warning(f"股票{symbol}数据不存在，无法卖出")
                continue
            
            stock_df = self.stock_data[symbol]
            stock_df['date'] = pd.to_datetime(stock_df['date']).dt.strftime('%Y-%m-%d')
            day_data = stock_df[stock_df['date'] == date]
            
            if day_data.empty:
                logger.warning(f"股票{symbol}在{date}没有数据，无法卖出")
                continue
            
            # 根据卖出类型确定价格
            if sell_type == 'open':
                price = day_data['open'].values[0]
            elif sell_type == 'vwap':
                # 成交量加权平均价 = 成交额 / 成交量
                if 'amount' in day_data.columns and 'volume' in day_data.columns:
                    price = day_data['amount'].values[0] / day_data['volume'].values[0]
                else:
                    # 如果没有成交额或成交量数据，使用开盘价和收盘价的平均值
                    price = (day_data['open'].values[0] + day_data['close'].values[0]) / 2
            else:
                # 默认使用开盘价
                price = day_data['open'].values[0]
            
            # 考虑滑点
            sell_price = price * (1 - self.slippage)
            
            # 计算卖出金额
            shares = position['amount']
            revenue = shares * sell_price
            commission = revenue * self.commission_rate
            net_revenue = revenue - commission
            
            # 更新资金
            self.current_capital += net_revenue
            
            # 计算收益
            cost = position['cost']
            profit = net_revenue - cost
            profit_rate = profit / cost
            
            # 记录交易
            self.trade_history.append({
                'date': date,
                'symbol': symbol,
                'action': 'sell',
                'price': sell_price,
                'shares': shares,
                'revenue': revenue,
                'commission': commission,
                'net_revenue': net_revenue,
                'profit': profit,
                'profit_rate': profit_rate
            })
            
            logger.info(f"{date} 卖出 {symbol}: {shares}股，价格{sell_price:.2f}，净收入{net_revenue:.2f}，收益率{profit_rate:.2%}")
            
            # 标记待移除的持仓
            symbols_to_remove.append(symbol)
        
        # 移除已卖出的持仓
        for symbol in symbols_to_remove:
            del self.positions[symbol]
    
    def calculate_daily_value(self, date: str):
        """
        计算每日总资产价值
        
        Args:
            date: 交易日期
        """
        # 现金部分
        total_value = self.current_capital
        
        # 持仓市值
        position_value = 0
        for symbol, position in self.positions.items():
            if symbol in self.stock_data:
                stock_df = self.stock_data[symbol]
                stock_df['date'] = pd.to_datetime(stock_df['date']).dt.strftime('%Y-%m-%d')
                day_data = stock_df[stock_df['date'] == date]
                
                if not day_data.empty:
                    price = day_data['close'].values[0]
                    shares = position['amount']
                    value = price * shares
                    position_value += value
        
        total_value += position_value
        
        # 记录每日资产
        self.daily_values.append({
            'date': date,
            'cash': self.current_capital,
            'position': position_value,
            'total': total_value
        })
        
        # 计算日收益率
        if len(self.daily_values) > 1:
            prev_value = self.daily_values[-2]['total']
            daily_return = (total_value - prev_value) / prev_value
            self.daily_returns.append({
                'date': date,
                'return': daily_return
            })
    
    def run_single_day(self, date: str, recommendations: pd.DataFrame, sell_type: str = 'open'):
        """
        运行单日回测
        
        Args:
            date: 交易日期
            recommendations: 推荐股票DataFrame，必须包含symbol和score列
            sell_type: 卖出类型，'open'表示开盘价卖出，'vwap'表示成交量加权平均价卖出
        """
        self.current_date = date
        
        # 先执行卖出（T+1日）
        self.execute_sell(date, sell_type)
        
        # 再执行买入（T日）
        self.execute_buy(date, recommendations)
        
        # 计算每日资产价值
        self.calculate_daily_value(date)
    
    def run_backtest(self, recommendations_by_date: Dict[str, pd.DataFrame], sell_type: str = 'open'):
        """
        运行完整回测
        
        Args:
            recommendations_by_date: 按日期索引的推荐股票字典，格式为 {date: recommendations_df}
            sell_type: 卖出类型，'open'表示开盘价卖出，'vwap'表示成交量加权平均价卖出
            
        Returns:
            回测结果字典
        """
        # 初始化回测状态
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.daily_returns = []
        self.daily_values = []
        
        # 记录初始资产
        self.daily_values.append({
            'date': self.trading_dates[0],
            'cash': self.initial_capital,
            'position': 0,
            'total': self.initial_capital
        })
        
        # 按日期顺序执行回测
        for date in self.trading_dates:
            if date in recommendations_by_date:
                recommendations = recommendations_by_date[date]
                self.run_single_day(date, recommendations, sell_type)
            else:
                # 如果当天没有推荐，只执行卖出和计算资产
                self.execute_sell(date, sell_type)
                self.calculate_daily_value(date)
        
        # 整理回测结果
        trades_df = pd.DataFrame(self.trade_history)
        daily_values_df = pd.DataFrame(self.daily_values)
        daily_returns_df = pd.DataFrame(self.daily_returns) if self.daily_returns else pd.DataFrame(columns=['date', 'return'])
        
        # 计算回测统计指标
        stats = self.calculate_stats()
        
        return {
            'trades': trades_df,
            'daily_values': daily_values_df,
            'daily_returns': daily_returns_df,
            'stats': stats,
            'final_positions': self.positions,
            'final_capital': self.current_capital
        }
    
    def calculate_stats(self) -> Dict[str, float]:
        """
        计算回测统计指标
        
        Returns:
            统计指标字典
        """
        # 提取交易记录
        buy_trades = [t for t in self.trade_history if t['action'] == 'buy']
        sell_trades = [t for t in self.trade_history if t['action'] == 'sell']
        
        # 计算总收益
        initial_value = self.initial_capital
        final_value = self.daily_values[-1]['total'] if self.daily_values else self.current_capital
        total_return = (final_value - initial_value) / initial_value
        
        # 计算胜率
        winning_trades = [t for t in sell_trades if t['profit'] > 0]
        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
        
        # 计算平均收益率
        avg_profit_rate = np.mean([t['profit_rate'] for t in sell_trades]) if sell_trades else 0
        
        # 计算最大回撤
        max_drawdown = 0
        peak_value = initial_value
        for value in self.daily_values:
            if value['total'] > peak_value:
                peak_value = value['total']
            else:
                drawdown = (peak_value - value['total']) / peak_value
                max_drawdown = max(max_drawdown, drawdown)
        
        # 计算年化收益率
        if self.trading_dates and len(self.trading_dates) > 1:
            start = datetime.strptime(self.trading_dates[0], '%Y-%m-%d')
            end = datetime.strptime(self.trading_dates[-1], '%Y-%m-%d')
            years = (end - start).days / 365
            annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        else:
            annualized_return = 0
        
        # 计算夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        if self.daily_returns:
            returns = [r['return'] for r in self.daily_returns]
            daily_risk_free = (1 + risk_free_rate) ** (1/252) - 1
            excess_returns = [r - daily_risk_free for r in returns]
            sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_profit_rate': avg_profit_rate,
            'sharpe_ratio': sharpe_ratio,
            'trade_count': len(sell_trades),
            'final_value': final_value
        }