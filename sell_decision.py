#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卖出决策模块
功能：对前一天推荐股票在次日9:45判断是否卖出，规则如涨超3%止盈，跌超3%止损
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import os
from data_fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SellDecision:
    """卖出决策类"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.sell_rules = {
            'profit_threshold': 3.0,  # 止盈阈值 3%
            'loss_threshold': -3.0,   # 止损阈值 -3%
            'hold_days_limit': 5,     # 最大持有天数
            'volume_check': True,     # 是否检查成交量
            'technical_check': True   # 是否进行技术面检查
        }
    
    def load_previous_recommendations(self, date: str = None) -> List[Dict]:
        """加载前一天的推荐结果"""
        if date is None:
            # 获取前一个交易日
            today = datetime.now()
            if today.weekday() == 0:  # 周一
                previous_date = (today - timedelta(days=3)).strftime('%Y%m%d')
            else:
                previous_date = (today - timedelta(days=1)).strftime('%Y%m%d')
        else:
            previous_date = date
        
        buy_file_path = f"result/buy_{previous_date}.json"
        
        if not os.path.exists(buy_file_path):
            logger.warning(f"未找到前一天的推荐文件: {buy_file_path}")
            return []
        
        try:
            with open(buy_file_path, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
            logger.info(f"加载了{len(recommendations)}只前日推荐股票")
            return recommendations
        except Exception as e:
            logger.error(f"加载推荐文件失败: {e}")
            return []
    
    def get_current_prices(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取当前股价信息"""
        try:
            current_data = self.data_fetcher.get_stock_realtime_data(stock_codes)
            return current_data
        except Exception as e:
            logger.error(f"获取当前股价失败: {e}")
            return {}
    
    def calculate_return_rate(self, buy_price: float, current_price: float) -> float:
        """计算收益率"""
        if buy_price <= 0:
            return 0
        return ((current_price - buy_price) / buy_price) * 100
    
    def check_basic_sell_conditions(self, stock_info: Dict, current_data: Dict) -> Tuple[bool, str]:
        """检查基本卖出条件"""
        buy_price = stock_info.get('current_price', 0)
        current_price = current_data.get('price', 0)
        
        if current_price <= 0 or buy_price <= 0:
            return True, "价格数据异常，建议卖出"
        
        return_rate = self.calculate_return_rate(buy_price, current_price)
        
        # 止盈条件
        if return_rate >= self.sell_rules['profit_threshold']:
            return True, f"达到止盈条件，收益率{return_rate:.2f}%"
        
        # 止损条件
        if return_rate <= self.sell_rules['loss_threshold']:
            return True, f"达到止损条件，收益率{return_rate:.2f}%"
        
        return False, f"收益率{return_rate:.2f}%，继续持有"
    
    def check_technical_sell_conditions(self, stock_code: str, current_data: Dict) -> Tuple[bool, str]:
        """检查技术面卖出条件"""
        if not self.sell_rules['technical_check']:
            return False, ""
        
        try:
            # 获取历史数据进行技术分析
            hist_data = self.data_fetcher.get_stock_history_data(stock_code, period=10)
            
            if hist_data.empty:
                return False, ""
            
            # 检查技术指标
            reasons = []
            
            # 检查成交量
            if self.sell_rules['volume_check']:
                current_volume = current_data.get('volume', 0)
                avg_volume = hist_data['成交量'].tail(5).mean()
                
                if current_volume > 0 and avg_volume > 0:
                    volume_ratio = current_volume / avg_volume
                    if volume_ratio > 3:  # 成交量异常放大
                        reasons.append("成交量异常放大")
            
            # 检查振幅
            amplitude = current_data.get('amplitude', 0)
            if amplitude > 8:  # 振幅过大
                reasons.append(f"振幅过大({amplitude:.1f}%)")
            
            # 检查是否连续下跌
            if len(hist_data) >= 3:
                recent_closes = hist_data['收盘'].tail(3).values
                if len(recent_closes) >= 3 and recent_closes[-1] < recent_closes[-2] < recent_closes[-3]:
                    reasons.append("连续下跌趋势")
            
            if reasons:
                return True, f"技术面风险: {', '.join(reasons)}"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"技术面分析失败: {e}")
            return False, ""
    
    def check_market_conditions(self) -> Tuple[bool, str]:
        """检查市场整体条件"""
        try:
            # 获取市场情绪数据
            market_sentiment = self.data_fetcher.get_market_sentiment_data()
            
            # 如果市场整体大跌，建议减仓
            down_ratio = market_sentiment.get('down_ratio', 0)
            if down_ratio > 0.7:  # 超过70%的股票下跌
                return True, "市场整体下跌，建议减仓"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"市场条件检查失败: {e}")
            return False, ""
    
    def calculate_position_size_adjustment(self, stock_info: Dict, current_data: Dict) -> Tuple[float, str]:
        """计算仓位调整建议"""
        buy_price = stock_info.get('current_price', 0)
        current_price = current_data.get('price', 0)
        
        if current_price <= 0 or buy_price <= 0:
            return 0, "全部卖出"
        
        return_rate = self.calculate_return_rate(buy_price, current_price)
        
        # 根据收益率调整仓位
        if return_rate > 5:  # 收益超过5%，减仓一半锁定利润
            return 0.5, "减仓50%锁定利润"
        elif return_rate < -1.5:  # 亏损超过1.5%，减仓降低风险
            return 0.3, "减仓30%降低风险"
        else:
            return 1.0, "维持仓位"
    
    def make_sell_decisions(self, recommendations: List[Dict]) -> List[Dict]:
        """制定卖出决策"""
        if not recommendations:
            return []
        
        logger.info("开始制定卖出决策...")
        
        # 获取股票代码列表
        stock_codes = [stock['stock_code'] for stock in recommendations]
        
        # 获取当前价格
        current_prices = self.get_current_prices(stock_codes)
        
        # 检查市场整体条件
        market_sell, market_reason = self.check_market_conditions()
        
        sell_decisions = []
        
        for stock_info in recommendations:
            stock_code = stock_info['stock_code']
            stock_name = stock_info.get('stock_name', '')
            
            try:
                current_data = current_prices.get(stock_code, {})
                
                if not current_data:
                    # 无法获取当前数据，建议卖出
                    decision = {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'action': 'SELL',
                        'sell_ratio': 1.0,
                        'reason': '无法获取当前价格数据',
                        'buy_price': stock_info.get('current_price', 0),
                        'current_price': 0,
                        'return_rate': 0,
                        'urgency': 'HIGH'
                    }
                    sell_decisions.append(decision)
                    continue
                
                # 检查基本卖出条件
                basic_sell, basic_reason = self.check_basic_sell_conditions(stock_info, current_data)
                
                # 检查技术面条件
                tech_sell, tech_reason = self.check_technical_sell_conditions(stock_code, current_data)
                
                # 计算仓位调整
                position_ratio, position_reason = self.calculate_position_size_adjustment(stock_info, current_data)
                
                # 综合决策
                buy_price = stock_info.get('current_price', 0)
                current_price = current_data.get('price', 0)
                return_rate = self.calculate_return_rate(buy_price, current_price)
                
                # 决定操作
                if basic_sell or tech_sell or market_sell:
                    action = 'SELL'
                    sell_ratio = 1.0
                    urgency = 'HIGH' if basic_sell else 'MEDIUM'
                    
                    reasons = [r for r in [basic_reason, tech_reason, market_reason] if r]
                    reason = '; '.join(reasons)
                    
                elif position_ratio < 1.0:
                    action = 'REDUCE'
                    sell_ratio = 1.0 - position_ratio
                    urgency = 'LOW'
                    reason = position_reason
                    
                else:
                    action = 'HOLD'
                    sell_ratio = 0
                    urgency = 'NONE'
                    reason = '继续持有，等待更好时机'
                
                decision = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'action': action,
                    'sell_ratio': sell_ratio,
                    'reason': reason,
                    'buy_price': buy_price,
                    'current_price': current_price,
                    'return_rate': round(return_rate, 2),
                    'urgency': urgency,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                sell_decisions.append(decision)
                
            except Exception as e:
                logger.error(f"股票{stock_code}卖出决策失败: {e}")
                continue
        
        logger.info(f"卖出决策完成，共处理{len(sell_decisions)}只股票")
        return sell_decisions
    
    def format_sell_results(self, sell_decisions: List[Dict]) -> Dict:
        """格式化卖出结果"""
        # 统计信息
        total_stocks = len(sell_decisions)
        sell_count = len([d for d in sell_decisions if d['action'] == 'SELL'])
        reduce_count = len([d for d in sell_decisions if d['action'] == 'REDUCE'])
        hold_count = len([d for d in sell_decisions if d['action'] == 'HOLD'])
        
        # 收益统计
        total_return = sum([d['return_rate'] for d in sell_decisions])
        avg_return = total_return / total_stocks if total_stocks > 0 else 0
        
        positive_returns = [d['return_rate'] for d in sell_decisions if d['return_rate'] > 0]
        negative_returns = [d['return_rate'] for d in sell_decisions if d['return_rate'] < 0]
        
        result = {
            'summary': {
                'total_stocks': total_stocks,
                'sell_count': sell_count,
                'reduce_count': reduce_count,
                'hold_count': hold_count,
                'avg_return_rate': round(avg_return, 2),
                'positive_count': len(positive_returns),
                'negative_count': len(negative_returns),
                'max_return': round(max([d['return_rate'] for d in sell_decisions]), 2) if sell_decisions else 0,
                'min_return': round(min([d['return_rate'] for d in sell_decisions]), 2) if sell_decisions else 0
            },
            'decisions': sell_decisions,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
    
    def execute_sell_analysis(self, date: str = None) -> Dict:
        """执行卖出分析"""
        logger.info("开始执行卖出分析...")
        
        # 加载前一天推荐
        recommendations = self.load_previous_recommendations(date)
        
        if not recommendations:
            return {
                'summary': {'total_stocks': 0},
                'decisions': [],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 制定卖出决策
        sell_decisions = self.make_sell_decisions(recommendations)
        
        # 格式化结果
        formatted_result = self.format_sell_results(sell_decisions)
        
        logger.info("卖出分析完成")
        return formatted_result

if __name__ == "__main__":
    # 测试代码
    sell_engine = SellDecision()
    
    # 创建测试推荐数据
    test_recommendations = [
        {
            'stock_code': '000001',
            'stock_name': '平安银行',
            'current_price': 15.68,
            'total_score': 85.2
        },
        {
            'stock_code': '000002',
            'stock_name': '万科A',
            'current_price': 28.45,
            'total_score': 72.1
        }
    ]
    
    # 执行卖出决策
    sell_decisions = sell_engine.make_sell_decisions(test_recommendations)
    formatted_result = sell_engine.format_sell_results(sell_decisions)
    
    print("卖出决策结果:")
    print(f"总计{formatted_result['summary']['total_stocks']}只股票")
    print(f"建议卖出: {formatted_result['summary']['sell_count']}只")
    print(f"建议减仓: {formatted_result['summary']['reduce_count']}只")
    print(f"继续持有: {formatted_result['summary']['hold_count']}只")
    print(f"平均收益率: {formatted_result['summary']['avg_return_rate']}%")
    
    for decision in sell_decisions:
        print(f"{decision['stock_name']}({decision['stock_code']}): {decision['action']} - {decision['reason']}")