#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尾盘买入策略
基于5分钟均线突破的尾盘买入策略
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, time

from .base_strategy import BaseStrategy
from ..core.logging import get_logger

logger = get_logger(__name__)


class EveningBuyStrategy(BaseStrategy):
    """尾盘买入策略
    
    策略逻辑:
    1. 在尾盘时段（14:30-15:00）监控股票
    2. 价格突破5日均线
    3. 成交量放大（超过平均成交量1.5倍）
    4. 涨幅适中（0-5%）
    5. 价格在合理区间（5-100元）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化尾盘买入策略"""
        default_config = {
            'ma_period': 5,                    # 均线周期
            'volume_threshold': 1.5,           # 成交量放大倍数
            'price_change_min': 0,             # 最小涨幅
            'price_change_max': 5,             # 最大涨幅
            'min_price': 5,                    # 最低价格
            'max_price': 100,                  # 最高价格
            'confidence_threshold': 60,        # 置信度阈值
            'evening_start_time': '14:30',     # 尾盘开始时间
            'evening_end_time': '15:00',       # 尾盘结束时间
            'risk_management': {
                'stop_loss_pct': 3.0,          # 止损比例
                'take_profit_pct': 5.0,        # 止盈比例
                'max_position_size': 10000     # 最大仓位金额
            }
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(default_config)
        
        logger.info(f"初始化尾盘买入策略，配置: {self.config}")
    
    async def generate_signals(
        self,
        stock_data: pd.DataFrame,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """生成买入信号
        
        Args:
            stock_data: 股票历史数据
            stock_code: 股票代码
            
        Returns:
            买入信号列表
        """
        try:
            if stock_data.empty or len(stock_data) < self.config['ma_period']:
                logger.warning(f"股票 {stock_code} 数据不足，无法生成信号")
                return []
            
            # 计算技术指标
            data_with_indicators = self.calculate_technical_indicators(stock_data)
            
            signals = []
            
            # 遍历数据，查找买入信号
            for i in range(self.config['ma_period'], len(data_with_indicators)):
                current_row = data_with_indicators.iloc[i]
                
                # 检查是否在尾盘时段
                if not self._is_evening_time(current_row.get('trade_time', '15:00')):
                    continue
                
                # 应用策略条件
                conditions = self._check_buy_conditions(data_with_indicators, i)
                
                # 计算置信度
                confidence = self.calculate_confidence_score(
                    conditions,
                    weights={
                        'price_above_ma': 30,
                        'volume_sufficient': 25,
                        'price_change_ok': 20,
                        'price_range_ok': 15,
                        'recent_performance': 10
                    }
                )
                
                # 生成信号
                if confidence >= self.config['confidence_threshold']:
                    signal = self._create_buy_signal(
                        stock_code,
                        current_row,
                        confidence,
                        conditions,
                        data_with_indicators.iloc[i-5:i+1]  # 最近6个数据点
                    )
                    
                    if self.validate_signal(signal, data_with_indicators):
                        signals.append(signal)
                        self.log_signal(signal)
            
            logger.info(f"股票 {stock_code} 生成了 {len(signals)} 个买入信号")
            return signals
            
        except Exception as e:
            logger.error(f"生成买入信号失败: {stock_code} - {str(e)}")
            return []
    
    def _check_buy_conditions(
        self,
        data: pd.DataFrame,
        index: int
    ) -> Dict[str, bool]:
        """检查买入条件
        
        Args:
            data: 包含技术指标的数据
            index: 当前数据索引
            
        Returns:
            条件检查结果
        """
        try:
            current = data.iloc[index]
            recent_data = data.iloc[max(0, index-10):index+1]
            
            # 条件1: 价格突破5日均线
            price_above_ma = current['close_price'] > current['ma5']
            
            # 条件2: 成交量放大
            volume_sufficient = current['volume_ratio'] >= self.config['volume_threshold']
            
            # 条件3: 涨幅适中
            pct_change = current.get('pct_change', 0)
            price_change_ok = (
                self.config['price_change_min'] <= pct_change <= self.config['price_change_max']
            )
            
            # 条件4: 价格在合理区间
            price_range_ok = (
                self.config['min_price'] <= current['close_price'] <= self.config['max_price']
            )
            
            # 条件5: 近期表现良好
            recent_performance = recent_data['pct_change'].mean() > -2
            
            return {
                'price_above_ma': price_above_ma,
                'volume_sufficient': volume_sufficient,
                'price_change_ok': price_change_ok,
                'price_range_ok': price_range_ok,
                'recent_performance': recent_performance
            }
            
        except Exception as e:
            logger.error(f"检查买入条件失败: {str(e)}")
            return {}
    
    def _create_buy_signal(
        self,
        stock_code: str,
        current_data: pd.Series,
        confidence: float,
        conditions: Dict[str, bool],
        recent_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """创建买入信号
        
        Args:
            stock_code: 股票代码
            current_data: 当前数据
            confidence: 置信度
            conditions: 触发条件
            recent_data: 最近数据
            
        Returns:
            买入信号
        """
        try:
            # 计算目标价和止损价
            current_price = float(current_data['close_price'])
            target_price = current_price * (1 + self.config['risk_management']['take_profit_pct'] / 100)
            stop_loss_price = current_price * (1 - self.config['risk_management']['stop_loss_pct'] / 100)
            
            # 技术指标
            indicators = {
                'ma5': float(current_data.get('ma5', 0)),
                'ma10': float(current_data.get('ma10', 0)),
                'ma20': float(current_data.get('ma20', 0)),
                'rsi': float(current_data.get('rsi', 50)),
                'volume_ratio': float(current_data.get('volume_ratio', 1)),
                'pct_change': float(current_data.get('pct_change', 0)),
                'macd': float(current_data.get('macd', 0)),
                'macd_signal': float(current_data.get('macd_signal', 0))
            }
            
            # 生成买入理由
            reason_parts = []
            if conditions.get('price_above_ma'):
                reason_parts.append(f"价格({current_price:.2f})突破5日均线({indicators['ma5']:.2f})")
            if conditions.get('volume_sufficient'):
                reason_parts.append(f"成交量放大{indicators['volume_ratio']:.1f}倍")
            if conditions.get('price_change_ok'):
                reason_parts.append(f"涨幅适中({indicators['pct_change']:.1f}%)")
            
            reason = "; ".join(reason_parts)
            
            signal = self.format_signal(
                stock_code=stock_code,
                signal_type='buy',
                price=current_price,
                confidence=confidence,
                conditions=conditions,
                indicators=indicators,
                timestamp=current_data.get('trade_date', datetime.now().strftime('%Y-%m-%d'))
            )
            
            # 添加策略特定信息
            signal.update({
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'expected_return': self.config['risk_management']['take_profit_pct'],
                'max_loss': self.config['risk_management']['stop_loss_pct'],
                'reason': reason,
                'strategy_type': 'evening_buy',
                'timeframe': '5min'
            })
            
            return signal
            
        except Exception as e:
            logger.error(f"创建买入信号失败: {str(e)}")
            return {}
    
    def validate_signal(
        self,
        signal: Dict[str, Any],
        stock_data: pd.DataFrame
    ) -> bool:
        """验证买入信号
        
        Args:
            signal: 买入信号
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
            if price <= 0 or price < self.config['min_price'] or price > self.config['max_price']:
                return False
            
            # 技术指标验证
            indicators = signal.get('indicators', {})
            
            # RSI不能过高（避免超买）
            if indicators.get('rsi', 50) > 80:
                logger.warning(f"RSI过高({indicators['rsi']:.1f})，跳过信号")
                return False
            
            # 成交量验证
            if indicators.get('volume_ratio', 0) < self.config['volume_threshold']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证买入信号失败: {str(e)}")
            return False
    
    def calculate_position_size(
        self,
        signal: Dict[str, Any],
        available_capital: float
    ) -> float:
        """计算建议仓位大小
        
        Args:
            signal: 买入信号
            available_capital: 可用资金
            
        Returns:
            建议投资金额
        """
        try:
            # 基于置信度和风险管理计算仓位
            confidence = signal.get('confidence', 0)
            max_position = self.config['risk_management']['max_position_size']
            
            # 置信度越高，仓位越大
            confidence_factor = min(confidence / 100, 1.0)
            
            # 基础仓位（可用资金的10%）
            base_position = available_capital * 0.1
            
            # 调整后的仓位
            suggested_position = base_position * confidence_factor
            
            # 不超过最大仓位限制
            final_position = min(suggested_position, max_position, available_capital * 0.2)
            
            logger.info(
                f"计算仓位: 置信度={confidence}%, "
                f"基础仓位={base_position:.0f}, "
                f"建议仓位={final_position:.0f}"
            )
            
            return final_position
            
        except Exception as e:
            logger.error(f"计算仓位大小失败: {str(e)}")
            return 0.0
    
    def _is_evening_time(self, trade_time: str) -> bool:
        """检查是否在尾盘时段
        
        Args:
            trade_time: 交易时间字符串 (HH:MM)
            
        Returns:
            是否在尾盘时段
        """
        try:
            if not trade_time or ':' not in trade_time:
                return True  # 如果没有时间信息，默认允许
            
            current_time = time.fromisoformat(trade_time)
            start_time = time.fromisoformat(self.config['evening_start_time'])
            end_time = time.fromisoformat(self.config['evening_end_time'])
            
            return start_time <= current_time <= end_time
            
        except Exception as e:
            logger.warning(f"检查尾盘时间失败: {str(e)}")
            return True  # 出错时默认允许
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        return (
            "尾盘5分钟均线突破买入策略：\n"
            "1. 监控尾盘时段（14:30-15:00）的股票\n"
            "2. 价格突破5日均线\n"
            "3. 成交量放大超过1.5倍\n"
            "4. 当日涨幅在0-5%之间\n"
            "5. 股价在5-100元合理区间\n"
            "6. 近期表现良好（平均涨跌幅>-2%）"
        )
    
    def get_risk_warnings(self) -> List[str]:
        """获取风险提示"""
        return [
            "尾盘买入存在隔夜风险",
            "需要关注次日开盘表现",
            "建议设置3%止损",
            "避免在市场极端波动时使用",
            "注意控制单笔投资金额"
        ]