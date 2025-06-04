#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
早盘卖出策略
基于高开高走形态的早盘卖出策略
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, time

from .base_strategy import BaseStrategy
from ..core.logging import get_logger

logger = get_logger(__name__)


class MorningSellStrategy(BaseStrategy):
    """早盘卖出策略
    
    策略逻辑:
    1. 在早盘时段（9:30-10:30）监控持仓股票
    2. 股票高开（开盘价高于前日收盘价）
    3. 高走（当前价格高于开盘价）
    4. 当日涨幅较大（>3%）
    5. 近期累计涨幅较大（>10%）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化早盘卖出策略"""
        default_config = {
            'min_gap_up': 1.0,                 # 最小高开幅度（%）
            'min_intraday_gain': 3.0,          # 最小当日涨幅（%）
            'cumulative_return_threshold': 10.0, # 累计涨幅阈值（%）
            'volume_amplification': 2.0,       # 成交量放大倍数
            'confidence_threshold': 70,        # 置信度阈值
            'morning_start_time': '09:30',     # 早盘开始时间
            'morning_end_time': '10:30',       # 早盘结束时间
            'lookback_days': 5,                # 回看天数
            'risk_management': {
                'take_profit_pct': 3.0,        # 止盈比例
                'max_holding_period': 30,      # 最大持有时间（分钟）
                'trailing_stop_pct': 1.0       # 移动止损比例
            }
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(default_config)
        
        logger.info(f"初始化早盘卖出策略，配置: {self.config}")
    
    async def generate_signals(
        self,
        stock_data: pd.DataFrame,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """生成卖出信号
        
        Args:
            stock_data: 股票历史数据
            stock_code: 股票代码
            
        Returns:
            卖出信号列表
        """
        try:
            if stock_data.empty or len(stock_data) < 2:
                logger.warning(f"股票 {stock_code} 数据不足，无法生成信号")
                return []
            
            # 计算技术指标
            data_with_indicators = self.calculate_technical_indicators(stock_data)
            
            signals = []
            
            # 遍历数据，查找卖出信号
            for i in range(1, len(data_with_indicators)):
                current_row = data_with_indicators.iloc[i]
                previous_row = data_with_indicators.iloc[i-1]
                
                # 检查是否在早盘时段
                if not self._is_morning_time(current_row.get('trade_time', '10:00')):
                    continue
                
                # 应用策略条件
                conditions = self._check_sell_conditions(
                    data_with_indicators, i, current_row, previous_row
                )
                
                # 计算置信度
                confidence = self.calculate_confidence_score(
                    conditions,
                    weights={
                        'gap_up_sufficient': 35,
                        'intraday_gain_ok': 30,
                        'cumulative_return_high': 25,
                        'volume_amplified': 10
                    }
                )
                
                # 生成信号
                if confidence >= self.config['confidence_threshold']:
                    signal = self._create_sell_signal(
                        stock_code,
                        current_row,
                        previous_row,
                        confidence,
                        conditions,
                        data_with_indicators.iloc[max(0, i-self.config['lookback_days']):i+1]
                    )
                    
                    if self.validate_signal(signal, data_with_indicators):
                        signals.append(signal)
                        self.log_signal(signal)
            
            logger.info(f"股票 {stock_code} 生成了 {len(signals)} 个卖出信号")
            return signals
            
        except Exception as e:
            logger.error(f"生成卖出信号失败: {stock_code} - {str(e)}")
            return []
    
    def _check_sell_conditions(
        self,
        data: pd.DataFrame,
        index: int,
        current: pd.Series,
        previous: pd.Series
    ) -> Dict[str, bool]:
        """检查卖出条件
        
        Args:
            data: 包含技术指标的数据
            index: 当前数据索引
            current: 当前数据
            previous: 前一日数据
            
        Returns:
            条件检查结果
        """
        try:
            # 计算高开幅度
            gap_up = (
                (current['open_price'] - previous['close_price']) / previous['close_price'] * 100
            )
            
            # 计算当日涨幅
            intraday_gain = current.get('pct_change', 0)
            
            # 计算累计涨幅（最近几天）
            lookback_data = data.iloc[max(0, index-self.config['lookback_days']):index+1]
            if len(lookback_data) > 1:
                cumulative_return = (
                    (lookback_data['close_price'].iloc[-1] / lookback_data['close_price'].iloc[0] - 1) * 100
                )
            else:
                cumulative_return = 0
            
            # 条件1: 高开幅度足够
            gap_up_sufficient = gap_up >= self.config['min_gap_up']
            
            # 条件2: 当日涨幅足够
            intraday_gain_ok = intraday_gain >= self.config['min_intraday_gain']
            
            # 条件3: 累计涨幅较高
            cumulative_return_high = cumulative_return >= self.config['cumulative_return_threshold']
            
            # 条件4: 成交量放大
            volume_amplified = current.get('volume_ratio', 1) >= self.config['volume_amplification']
            
            # 条件5: 高开高走形态
            high_open_high_go = (
                current['open_price'] > previous['close_price'] and
                current['close_price'] > current['open_price']
            )
            
            return {
                'gap_up_sufficient': gap_up_sufficient,
                'intraday_gain_ok': intraday_gain_ok,
                'cumulative_return_high': cumulative_return_high,
                'volume_amplified': volume_amplified,
                'high_open_high_go': high_open_high_go,
                'gap_up_value': gap_up,
                'intraday_gain_value': intraday_gain,
                'cumulative_return_value': cumulative_return
            }
            
        except Exception as e:
            logger.error(f"检查卖出条件失败: {str(e)}")
            return {}
    
    def _create_sell_signal(
        self,
        stock_code: str,
        current_data: pd.Series,
        previous_data: pd.Series,
        confidence: float,
        conditions: Dict[str, Any],
        recent_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """创建卖出信号
        
        Args:
            stock_code: 股票代码
            current_data: 当前数据
            previous_data: 前一日数据
            confidence: 置信度
            conditions: 触发条件
            recent_data: 最近数据
            
        Returns:
            卖出信号
        """
        try:
            # 计算目标价
            current_price = float(current_data['close_price'])
            target_price = current_price * (1 + self.config['risk_management']['take_profit_pct'] / 100)
            
            # 技术指标
            indicators = {
                'gap_up': conditions.get('gap_up_value', 0),
                'intraday_gain': conditions.get('intraday_gain_value', 0),
                'cumulative_return': conditions.get('cumulative_return_value', 0),
                'volume_ratio': float(current_data.get('volume_ratio', 1)),
                'rsi': float(current_data.get('rsi', 50)),
                'ma5': float(current_data.get('ma5', 0)),
                'ma10': float(current_data.get('ma10', 0)),
                'macd': float(current_data.get('macd', 0))
            }
            
            # 生成卖出理由
            reason_parts = []
            if conditions.get('gap_up_sufficient'):
                reason_parts.append(f"高开{indicators['gap_up']:.1f}%")
            if conditions.get('intraday_gain_ok'):
                reason_parts.append(f"当日涨幅{indicators['intraday_gain']:.1f}%")
            if conditions.get('cumulative_return_high'):
                reason_parts.append(f"累计涨幅{indicators['cumulative_return']:.1f}%")
            if conditions.get('high_open_high_go'):
                reason_parts.append("高开高走形态")
            
            reason = "; ".join(reason_parts)
            
            signal = self.format_signal(
                stock_code=stock_code,
                signal_type='sell',
                price=current_price,
                confidence=confidence,
                conditions=conditions,
                indicators=indicators,
                timestamp=current_data.get('trade_date', datetime.now().strftime('%Y-%m-%d'))
            )
            
            # 添加策略特定信息
            signal.update({
                'target_price': target_price,
                'expected_return': self.config['risk_management']['take_profit_pct'],
                'reason': reason,
                'strategy_type': 'morning_sell',
                'timeframe': '1min',
                'urgency': self._calculate_urgency(indicators),
                'holding_period_limit': self.config['risk_management']['max_holding_period']
            })
            
            return signal
            
        except Exception as e:
            logger.error(f"创建卖出信号失败: {str(e)}")
            return {}
    
    def _calculate_urgency(self, indicators: Dict[str, float]) -> str:
        """计算卖出紧急程度
        
        Args:
            indicators: 技术指标
            
        Returns:
            紧急程度 (low/medium/high)
        """
        try:
            urgency_score = 0
            
            # RSI过高增加紧急程度
            if indicators.get('rsi', 50) > 80:
                urgency_score += 3
            elif indicators.get('rsi', 50) > 70:
                urgency_score += 2
            
            # 涨幅过大增加紧急程度
            if indicators.get('intraday_gain', 0) > 8:
                urgency_score += 3
            elif indicators.get('intraday_gain', 0) > 5:
                urgency_score += 2
            
            # 累计涨幅过大增加紧急程度
            if indicators.get('cumulative_return', 0) > 20:
                urgency_score += 2
            elif indicators.get('cumulative_return', 0) > 15:
                urgency_score += 1
            
            if urgency_score >= 6:
                return 'high'
            elif urgency_score >= 3:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"计算紧急程度失败: {str(e)}")
            return 'medium'
    
    def validate_signal(
        self,
        signal: Dict[str, Any],
        stock_data: pd.DataFrame
    ) -> bool:
        """验证卖出信号
        
        Args:
            signal: 卖出信号
            stock_data: 股票数据
            
        Returns:
            信号是否有效
        """
        try:
            # 基本验证
            if not signal or signal.get('confidence', 0) < self.config['confidence_threshold']:
                return False
            
            # 价格验证
            price = signal.get('price', 0)
            if price <= 0:
                return False
            
            # 技术指标验证
            indicators = signal.get('indicators', {})
            conditions = signal.get('conditions', {})
            
            # 必须满足高开条件
            if not conditions.get('gap_up_sufficient', False):
                return False
            
            # 必须满足当日涨幅条件
            if not conditions.get('intraday_gain_ok', False):
                return False
            
            # 避免在RSI过低时卖出（可能还有上涨空间）
            if indicators.get('rsi', 50) < 30:
                logger.warning(f"RSI过低({indicators['rsi']:.1f})，跳过卖出信号")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证卖出信号失败: {str(e)}")
            return False
    
    def calculate_position_size(
        self,
        signal: Dict[str, Any],
        available_capital: float
    ) -> float:
        """计算建议卖出比例
        
        Args:
            signal: 卖出信号
            available_capital: 可用资金（这里指持仓市值）
            
        Returns:
            建议卖出比例 (0-1)
        """
        try:
            confidence = signal.get('confidence', 0)
            urgency = signal.get('urgency', 'medium')
            indicators = signal.get('indicators', {})
            
            # 基础卖出比例
            base_ratio = 0.5  # 默认卖出50%
            
            # 根据置信度调整
            confidence_factor = confidence / 100
            
            # 根据紧急程度调整
            urgency_factors = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.3
            }
            urgency_factor = urgency_factors.get(urgency, 1.0)
            
            # 根据RSI调整（RSI越高，卖出比例越大）
            rsi = indicators.get('rsi', 50)
            if rsi > 80:
                rsi_factor = 1.2
            elif rsi > 70:
                rsi_factor = 1.1
            else:
                rsi_factor = 1.0
            
            # 计算最终卖出比例
            sell_ratio = base_ratio * confidence_factor * urgency_factor * rsi_factor
            
            # 限制在合理范围内
            sell_ratio = max(0.2, min(1.0, sell_ratio))
            
            logger.info(
                f"计算卖出比例: 置信度={confidence}%, "
                f"紧急程度={urgency}, RSI={rsi:.1f}, "
                f"建议卖出比例={sell_ratio:.1%}"
            )
            
            return sell_ratio
            
        except Exception as e:
            logger.error(f"计算卖出比例失败: {str(e)}")
            return 0.5  # 默认卖出50%
    
    def _is_morning_time(self, trade_time: str) -> bool:
        """检查是否在早盘时段
        
        Args:
            trade_time: 交易时间字符串 (HH:MM)
            
        Returns:
            是否在早盘时段
        """
        try:
            if not trade_time or ':' not in trade_time:
                return True  # 如果没有时间信息，默认允许
            
            current_time = time.fromisoformat(trade_time)
            start_time = time.fromisoformat(self.config['morning_start_time'])
            end_time = time.fromisoformat(self.config['morning_end_time'])
            
            return start_time <= current_time <= end_time
            
        except Exception as e:
            logger.warning(f"检查早盘时间失败: {str(e)}")
            return True  # 出错时默认允许
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        return (
            "早盘高开高走止盈策略：\n"
            "1. 监控早盘时段（9:30-10:30）的持仓股票\n"
            "2. 股票高开（开盘价高于前日收盘价1%以上）\n"
            "3. 高走（当前价格高于开盘价）\n"
            "4. 当日涨幅较大（>3%）\n"
            "5. 近期累计涨幅较大（>10%）\n"
            "6. 成交量放大（>2倍平均成交量）"
        )
    
    def get_risk_warnings(self) -> List[str]:
        """获取风险提示"""
        return [
            "早盘卖出可能错过后续上涨机会",
            "建议分批卖出，避免一次性清仓",
            "关注市场整体走势",
            "设置移动止损保护利润",
            "避免在重大利好消息发布时使用"
        ]
    
    def should_hold_longer(
        self,
        current_data: pd.Series,
        signal: Dict[str, Any]
    ) -> bool:
        """判断是否应该继续持有
        
        Args:
            current_data: 当前数据
            signal: 原始卖出信号
            
        Returns:
            是否应该继续持有
        """
        try:
            # 如果股票继续强势上涨，可以考虑继续持有
            current_gain = current_data.get('pct_change', 0)
            rsi = current_data.get('rsi', 50)
            
            # 强势上涨且RSI未过热
            if current_gain > 5 and rsi < 75:
                logger.info(f"股票继续强势上涨({current_gain:.1f}%)，建议继续持有")
                return True
            
            # 成交量持续放大
            volume_ratio = current_data.get('volume_ratio', 1)
            if volume_ratio > 3:
                logger.info(f"成交量持续放大({volume_ratio:.1f}倍)，建议继续持有")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"判断是否继续持有失败: {str(e)}")
            return False