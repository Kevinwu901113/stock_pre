#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版卖出信号判断模块
专门用于对前一日推荐股票在次日9:45时进行精确的止盈/止损判断
包含主力资金流出检测、情绪转空判断等高级功能
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import os
from enum import Enum
from data_fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SellSignalType(Enum):
    """卖出信号类型"""
    PROFIT_TAKING = "止盈"
    STOP_LOSS = "止损"
    FUND_OUTFLOW = "主力流出"
    SENTIMENT_TURN = "情绪转空"
    TECHNICAL_BREAK = "技术破位"
    VOLUME_ANOMALY = "成交量异常"
    MARKET_CRASH = "市场暴跌"
    RISK_CONTROL = "风险控制"

class SellAction(Enum):
    """卖出操作类型"""
    HOLD = "持有"
    REDUCE_25 = "减仓25%"
    REDUCE_50 = "减仓50%"
    REDUCE_75 = "减仓75%"
    SELL_ALL = "全部卖出"

class EnhancedSellSignal:
    """增强版卖出信号判断器"""
    
    def __init__(self, config_file: str = None):
        self.data_fetcher = DataFetcher()
        self.config = self._load_config(config_file)
        
        # 默认配置
        self.default_rules = {
            # 基础止盈止损
            'profit_threshold': 3.0,      # 开盘止盈阈值 3%
            'stop_loss_threshold': -3.0,  # 开盘止损阈值 -3%
            'quick_profit_threshold': 5.0, # 快速止盈阈值 5%
            'emergency_stop_threshold': -5.0, # 紧急止损阈值 -5%
            
            # 主力资金流出
            'major_outflow_threshold': -50000000,  # 主力净流出5000万
            'outflow_ratio_threshold': 0.7,        # 流出比例70%
            'continuous_outflow_days': 2,          # 连续流出天数
            
            # 情绪指标
            'sentiment_threshold': 30,             # 情绪指数阈值
            'panic_threshold': 20,                 # 恐慌阈值
            'market_fear_threshold': 0.6,          # 市场恐慌比例
            
            # 技术指标
            'volume_spike_ratio': 3.0,             # 成交量放大倍数
            'amplitude_threshold': 8.0,            # 振幅阈值
            'rsi_oversold': 20,                    # RSI超卖
            'rsi_overbought': 80,                  # RSI超买
            
            # 时间控制
            'check_time': '09:45',                 # 检查时间
            'max_hold_days': 5,                    # 最大持有天数
        }
        
        # 合并配置
        self.rules = {**self.default_rules, **self.config}
        
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}，使用默认配置")
        return {}
    
    def load_yesterday_recommendations(self, date: str = None) -> List[Dict]:
        """加载昨日推荐股票列表"""
        if date is None:
            # 自动计算前一个交易日
            today = datetime.now()
            if today.weekday() == 0:  # 周一
                target_date = (today - timedelta(days=3)).strftime('%Y%m%d')
            else:
                target_date = (today - timedelta(days=1)).strftime('%Y%m%d')
        else:
            target_date = date
        
        # 尝试多种文件路径
        possible_paths = [
            f"result/buy_{target_date}.json",
            f"results/fusion_results_{target_date}.json",
            f"results/enhanced_fusion_consensus_boost_{target_date}.json"
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 处理不同格式的推荐文件
                    if isinstance(data, dict) and 'recommendations' in data:
                        recommendations = data['recommendations']
                    elif isinstance(data, list):
                        recommendations = data
                    else:
                        continue
                    
                    logger.info(f"成功加载昨日推荐: {file_path}, 共{len(recommendations)}只股票")
                    return recommendations
                    
                except Exception as e:
                    logger.error(f"读取推荐文件失败 {file_path}: {e}")
                    continue
        
        logger.warning(f"未找到日期 {target_date} 的推荐文件")
        return []
    
    def get_opening_market_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取开盘行情数据"""
        try:
            # 获取实时数据
            realtime_data = self.data_fetcher.get_stock_realtime_data(stock_codes)
            
            # 获取昨日收盘价用于计算涨跌幅
            yesterday_data = {}
            for code in stock_codes:
                try:
                    hist_data = self.data_fetcher.get_stock_history_data(code, period=2)
                    if not hist_data.empty and len(hist_data) >= 2:
                        yesterday_data[code] = hist_data.iloc[-2]['收盘']
                except:
                    yesterday_data[code] = None
            
            # 合并数据
            market_data = {}
            for code in stock_codes:
                if code in realtime_data:
                    current_price = realtime_data[code].get('price', 0)
                    yesterday_close = yesterday_data.get(code, 0)
                    
                    if current_price > 0 and yesterday_close > 0:
                        change_pct = ((current_price - yesterday_close) / yesterday_close) * 100
                    else:
                        change_pct = 0
                    
                    market_data[code] = {
                        'current_price': current_price,
                        'yesterday_close': yesterday_close,
                        'change_percent': change_pct,
                        'volume': realtime_data[code].get('volume', 0),
                        'turnover': realtime_data[code].get('turnover', 0),
                        'amplitude': realtime_data[code].get('amplitude', 0),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取开盘行情数据失败: {e}")
            return {}
    
    def check_profit_loss_signals(self, stock_info: Dict, market_data: Dict) -> Tuple[bool, SellSignalType, str, SellAction]:
        """检查止盈止损信号"""
        change_pct = market_data.get('change_percent', 0)
        
        # 紧急止损
        if change_pct <= self.rules['emergency_stop_threshold']:
            return True, SellSignalType.STOP_LOSS, f"紧急止损，开盘跌幅{change_pct:.2f}%", SellAction.SELL_ALL
        
        # 快速止盈
        if change_pct >= self.rules['quick_profit_threshold']:
            return True, SellSignalType.PROFIT_TAKING, f"快速止盈，开盘涨幅{change_pct:.2f}%", SellAction.REDUCE_75
        
        # 标准止盈
        if change_pct >= self.rules['profit_threshold']:
            return True, SellSignalType.PROFIT_TAKING, f"达到止盈条件，开盘涨幅{change_pct:.2f}%", SellAction.REDUCE_50
        
        # 标准止损
        if change_pct <= self.rules['stop_loss_threshold']:
            return True, SellSignalType.STOP_LOSS, f"达到止损条件，开盘跌幅{change_pct:.2f}%", SellAction.SELL_ALL
        
        return False, None, "", SellAction.HOLD
    
    def check_fund_flow_signals(self, stock_code: str) -> Tuple[bool, SellSignalType, str, SellAction]:
        """检查主力资金流出信号"""
        try:
            # 获取资金流向数据
            fund_flow = self.data_fetcher.get_capital_flow_data(stock_code, period=3)
            
            if fund_flow.empty:
                return False, None, "", SellAction.HOLD
            
            # 检查今日主力净流出
            today_main_flow = fund_flow.iloc[-1].get('主力净流入', 0)
            
            if today_main_flow < self.rules['major_outflow_threshold']:
                return True, SellSignalType.FUND_OUTFLOW, \
                       f"主力大幅流出{abs(today_main_flow/10000):.0f}万元", SellAction.REDUCE_75
            
            # 检查连续流出
            if len(fund_flow) >= self.rules['continuous_outflow_days']:
                recent_flows = fund_flow.tail(self.rules['continuous_outflow_days'])['主力净流入']
                if all(flow < 0 for flow in recent_flows):
                    total_outflow = recent_flows.sum()
                    return True, SellSignalType.FUND_OUTFLOW, \
                           f"连续{self.rules['continuous_outflow_days']}日主力流出{abs(total_outflow/10000):.0f}万", SellAction.REDUCE_50
            
            # 检查流出比例
            total_flow = abs(fund_flow.iloc[-1].get('主力净流入', 0))
            if total_flow > 0:
                outflow_ratio = abs(min(0, today_main_flow)) / total_flow
                if outflow_ratio > self.rules['outflow_ratio_threshold']:
                    return True, SellSignalType.FUND_OUTFLOW, \
                           f"主力流出比例{outflow_ratio:.1%}", SellAction.REDUCE_25
            
            return False, None, "", SellAction.HOLD
            
        except Exception as e:
            logger.error(f"资金流向检查失败 {stock_code}: {e}")
            return False, None, "", SellAction.HOLD
    
    def check_sentiment_signals(self, stock_code: str) -> Tuple[bool, SellSignalType, str, SellAction]:
        """检查情绪转空信号"""
        try:
            # 获取市场情绪数据
            sentiment_data = self.data_fetcher.get_market_sentiment_data()
            
            # 检查个股情绪
            stock_sentiment = sentiment_data.get('stocks', {}).get(stock_code, {})
            sentiment_score = stock_sentiment.get('sentiment_score', 50)
            
            # 恐慌性抛售
            if sentiment_score <= self.rules['panic_threshold']:
                return True, SellSignalType.SENTIMENT_TURN, \
                       f"情绪恐慌，情绪指数{sentiment_score}", SellAction.SELL_ALL
            
            # 情绪显著转空
            if sentiment_score <= self.rules['sentiment_threshold']:
                return True, SellSignalType.SENTIMENT_TURN, \
                       f"情绪转空，情绪指数{sentiment_score}", SellAction.REDUCE_50
            
            # 检查市场整体恐慌
            market_fear_ratio = sentiment_data.get('fear_ratio', 0)
            if market_fear_ratio > self.rules['market_fear_threshold']:
                return True, SellSignalType.SENTIMENT_TURN, \
                       f"市场恐慌，恐慌比例{market_fear_ratio:.1%}", SellAction.REDUCE_25
            
            return False, None, "", SellAction.HOLD
            
        except Exception as e:
            logger.error(f"情绪检查失败 {stock_code}: {e}")
            return False, None, "", SellAction.HOLD
    
    def check_technical_signals(self, stock_code: str, market_data: Dict) -> Tuple[bool, SellSignalType, str, SellAction]:
        """检查技术面信号"""
        try:
            reasons = []
            max_action = SellAction.HOLD
            
            # 检查成交量异常
            current_volume = market_data.get('volume', 0)
            if current_volume > 0:
                hist_data = self.data_fetcher.get_stock_history_data(stock_code, period=5)
                if not hist_data.empty:
                    avg_volume = hist_data['成交量'].mean()
                    if avg_volume > 0:
                        volume_ratio = current_volume / avg_volume
                        if volume_ratio > self.rules['volume_spike_ratio']:
                            reasons.append(f"成交量异常放大{volume_ratio:.1f}倍")
                            max_action = max(max_action, SellAction.REDUCE_25, key=lambda x: x.value)
            
            # 检查振幅异常
            amplitude = market_data.get('amplitude', 0)
            if amplitude > self.rules['amplitude_threshold']:
                reasons.append(f"振幅过大{amplitude:.1f}%")
                max_action = max(max_action, SellAction.REDUCE_25, key=lambda x: x.value)
            
            # 检查技术破位
            change_pct = market_data.get('change_percent', 0)
            if change_pct < -2:  # 跌幅超过2%但未达到止损线
                hist_data = self.data_fetcher.get_stock_history_data(stock_code, period=10)
                if not hist_data.empty and len(hist_data) >= 5:
                    # 检查是否跌破重要支撑
                    recent_low = hist_data['最低'].tail(5).min()
                    current_price = market_data.get('current_price', 0)
                    if current_price > 0 and current_price < recent_low * 0.98:
                        reasons.append("跌破重要支撑位")
                        max_action = max(max_action, SellAction.REDUCE_50, key=lambda x: x.value)
            
            if reasons:
                return True, SellSignalType.TECHNICAL_BREAK, \
                       f"技术面风险: {'; '.join(reasons)}", max_action
            
            return False, None, "", SellAction.HOLD
            
        except Exception as e:
            logger.error(f"技术面检查失败 {stock_code}: {e}")
            return False, None, "", SellAction.HOLD
    
    def generate_sell_decision(self, stock_info: Dict, market_data: Dict) -> Dict:
        """生成单只股票的卖出决策"""
        stock_code = stock_info.get('stock_code', '')
        stock_name = stock_info.get('stock_name', '')
        
        # 初始化决策结果
        decision = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'current_price': market_data.get('current_price', 0),
            'yesterday_close': market_data.get('yesterday_close', 0),
            'change_percent': market_data.get('change_percent', 0),
            'volume': market_data.get('volume', 0),
            'amplitude': market_data.get('amplitude', 0),
            'action': SellAction.HOLD.value,
            'sell_ratio': 0,
            'signal_type': None,
            'reason': '继续持有',
            'urgency': 'LOW',
            'confidence': 0.5,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 按优先级检查各种信号
        signals = []
        
        # 1. 止盈止损信号（最高优先级）
        has_signal, signal_type, reason, action = self.check_profit_loss_signals(stock_info, market_data)
        if has_signal:
            signals.append((signal_type, reason, action, 0.9))
        
        # 2. 主力资金流出信号
        has_signal, signal_type, reason, action = self.check_fund_flow_signals(stock_code)
        if has_signal:
            signals.append((signal_type, reason, action, 0.8))
        
        # 3. 情绪转空信号
        has_signal, signal_type, reason, action = self.check_sentiment_signals(stock_code)
        if has_signal:
            signals.append((signal_type, reason, action, 0.7))
        
        # 4. 技术面信号
        has_signal, signal_type, reason, action = self.check_technical_signals(stock_code, market_data)
        if has_signal:
            signals.append((signal_type, reason, action, 0.6))
        
        # 选择最强信号
        if signals:
            # 按置信度排序，选择最强信号
            signals.sort(key=lambda x: x[3], reverse=True)
            best_signal = signals[0]
            
            decision.update({
                'signal_type': best_signal[0].value,
                'reason': best_signal[1],
                'action': best_signal[2].value,
                'confidence': best_signal[3]
            })
            
            # 设置卖出比例
            if best_signal[2] == SellAction.SELL_ALL:
                decision['sell_ratio'] = 1.0
                decision['urgency'] = 'HIGH'
            elif best_signal[2] == SellAction.REDUCE_75:
                decision['sell_ratio'] = 0.75
                decision['urgency'] = 'HIGH'
            elif best_signal[2] == SellAction.REDUCE_50:
                decision['sell_ratio'] = 0.5
                decision['urgency'] = 'MEDIUM'
            elif best_signal[2] == SellAction.REDUCE_25:
                decision['sell_ratio'] = 0.25
                decision['urgency'] = 'LOW'
        
        return decision
    
    def analyze_sell_signals(self, date: str = None) -> Dict:
        """分析卖出信号（主入口函数）"""
        logger.info(f"开始分析卖出信号 - 检查时间: {datetime.now().strftime('%H:%M')}")
        
        # 检查时间（可选）
        current_time = datetime.now().strftime('%H:%M')
        if current_time < '09:30' or current_time > '15:00':
            logger.warning(f"当前时间 {current_time} 不在交易时间内")
        
        # 加载昨日推荐
        recommendations = self.load_yesterday_recommendations(date)
        if not recommendations:
            return {
                'summary': {
                    'total_stocks': 0,
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': '未找到昨日推荐数据'
                },
                'decisions': []
            }
        
        # 获取股票代码列表
        stock_codes = [stock.get('stock_code', '') for stock in recommendations if stock.get('stock_code')]
        
        # 获取开盘行情数据
        market_data = self.get_opening_market_data(stock_codes)
        
        # 生成卖出决策
        decisions = []
        for stock_info in recommendations:
            stock_code = stock_info.get('stock_code', '')
            if stock_code in market_data:
                decision = self.generate_sell_decision(stock_info, market_data[stock_code])
                decisions.append(decision)
            else:
                # 无法获取行情数据的股票
                decision = {
                    'stock_code': stock_code,
                    'stock_name': stock_info.get('stock_name', ''),
                    'action': SellAction.SELL_ALL.value,
                    'sell_ratio': 1.0,
                    'signal_type': SellSignalType.RISK_CONTROL.value,
                    'reason': '无法获取行情数据，风险控制',
                    'urgency': 'HIGH',
                    'confidence': 0.8,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                decisions.append(decision)
        
        # 生成汇总统计
        summary = self._generate_summary(decisions)
        
        result = {
            'summary': summary,
            'decisions': decisions,
            'config': self.rules,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"卖出信号分析完成，共分析{len(decisions)}只股票")
        return result
    
    def _generate_summary(self, decisions: List[Dict]) -> Dict:
        """生成汇总统计"""
        total_stocks = len(decisions)
        
        # 按操作类型统计
        action_counts = {}
        for decision in decisions:
            action = decision['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # 按信号类型统计
        signal_counts = {}
        for decision in decisions:
            signal_type = decision.get('signal_type')
            if signal_type:
                signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
        
        # 按紧急程度统计
        urgency_counts = {}
        for decision in decisions:
            urgency = decision.get('urgency', 'LOW')
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        
        # 收益统计
        returns = [d.get('change_percent', 0) for d in decisions]
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]
        
        return {
            'total_stocks': total_stocks,
            'action_distribution': action_counts,
            'signal_distribution': signal_counts,
            'urgency_distribution': urgency_counts,
            'return_stats': {
                'avg_return': round(np.mean(returns), 2) if returns else 0,
                'max_return': round(max(returns), 2) if returns else 0,
                'min_return': round(min(returns), 2) if returns else 0,
                'positive_count': len(positive_returns),
                'negative_count': len(negative_returns),
                'positive_ratio': round(len(positive_returns) / total_stocks, 2) if total_stocks > 0 else 0
            },
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def save_results(self, results: Dict, output_dir: str = "results") -> str:
        """保存分析结果"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/sell_signals_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"卖出信号分析结果已保存: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return ""

def main():
    """主函数 - 演示用法"""
    print("🚨 增强版卖出信号判断系统")
    print("=" * 60)
    
    # 初始化卖出信号分析器
    sell_analyzer = EnhancedSellSignal()
    
    # 执行分析
    results = sell_analyzer.analyze_sell_signals()
    
    # 显示结果
    summary = results['summary']
    decisions = results['decisions']
    
    print(f"\n📊 分析汇总 ({summary['analysis_time']})")
    print(f"总计股票: {summary['total_stocks']}只")
    
    if summary['total_stocks'] > 0:
        print(f"\n📈 收益统计:")
        stats = summary['return_stats']
        print(f"  平均涨跌幅: {stats['avg_return']}%")
        print(f"  最大涨幅: {stats['max_return']}%")
        print(f"  最大跌幅: {stats['min_return']}%")
        print(f"  上涨股票: {stats['positive_count']}只 ({stats['positive_ratio']:.1%})")
        print(f"  下跌股票: {stats['negative_count']}只")
        
        print(f"\n🎯 操作建议分布:")
        for action, count in summary['action_distribution'].items():
            print(f"  {action}: {count}只")
        
        print(f"\n⚠️ 信号类型分布:")
        for signal, count in summary['signal_distribution'].items():
            print(f"  {signal}: {count}只")
        
        print(f"\n🔥 紧急程度分布:")
        for urgency, count in summary['urgency_distribution'].items():
            print(f"  {urgency}: {count}只")
        
        print(f"\n📋 详细决策 (前10只):")
        print("-" * 80)
        for i, decision in enumerate(decisions[:10]):
            urgency_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(decision.get('urgency'), "")
            print(f"{i+1:2d}. {decision['stock_name']}({decision['stock_code']}) {urgency_icon}")
            print(f"     涨跌幅: {decision.get('change_percent', 0):+.2f}% | 操作: {decision['action']}")
            print(f"     信号: {decision.get('signal_type', 'N/A')} | 理由: {decision['reason']}")
            print()
    
    # 保存结果
    filename = sell_analyzer.save_results(results)
    if filename:
        print(f"\n💾 详细结果已保存: {filename}")
    
    print("\n" + "=" * 60)
    print("🎯 卖出信号分析完成！")

if __name__ == "__main__":
    main()