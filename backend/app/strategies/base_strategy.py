#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础策略抽象类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

from ..core.logging import get_logger
from ..models.strategy import StrategySignal, StrategyConfig

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化策略"""
        self.config = config or {}
        self.name = self.__class__.__name__
        self.signals = []
        self.performance_metrics = {}
        
        logger.info(f"初始化策略: {self.name}")
    
    @abstractmethod
    async def generate_signals(
        self,
        stock_data: pd.DataFrame,
        stock_code: str
    ) -> List[Dict[str, Any]]:
        """生成交易信号
        
        Args:
            stock_data: 股票历史数据
            stock_code: 股票代码
            
        Returns:
            交易信号列表
        """
        pass
    
    @abstractmethod
    def validate_signal(
        self,
        signal: Dict[str, Any],
        stock_data: pd.DataFrame
    ) -> bool:
        """验证交易信号
        
        Args:
            signal: 交易信号
            stock_data: 股票数据
            
        Returns:
            信号是否有效
        """
        pass
    
    @abstractmethod
    def calculate_position_size(
        self,
        signal: Dict[str, Any],
        available_capital: float
    ) -> float:
        """计算仓位大小
        
        Args:
            signal: 交易信号
            available_capital: 可用资金
            
        Returns:
            建议仓位大小
        """
        pass
    
    def get_risk_management_rules(self) -> Dict[str, Any]:
        """获取风险管理规则"""
        return self.config.get('risk_management', {
            'max_position_size': 0.1,  # 最大仓位比例
            'stop_loss_pct': 0.05,     # 止损比例
            'take_profit_pct': 0.1,    # 止盈比例
            'max_drawdown': 0.2        # 最大回撤
        })
    
    def calculate_technical_indicators(
        self,
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """计算技术指标
        
        Args:
            data: 股票数据
            
        Returns:
            包含技术指标的数据框
        """
        try:
            df = data.copy()
            
            # 移动平均线
            df['ma5'] = df['close_price'].rolling(window=5).mean()
            df['ma10'] = df['close_price'].rolling(window=10).mean()
            df['ma20'] = df['close_price'].rolling(window=20).mean()
            
            # RSI
            df['rsi'] = self._calculate_rsi(df['close_price'])
            
            # MACD
            macd_data = self._calculate_macd(df['close_price'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
            
            # 布林带
            bollinger_data = self._calculate_bollinger_bands(df['close_price'])
            df['bb_upper'] = bollinger_data['upper']
            df['bb_middle'] = bollinger_data['middle']
            df['bb_lower'] = bollinger_data['lower']
            
            # 成交量指标
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            return df
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            logger.error(f"计算RSI失败: {str(e)}")
            return pd.Series(index=prices.index, dtype=float)
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """计算MACD指标"""
        try:
            ema_fast = prices.ewm(span=fast_period).mean()
            ema_slow = prices.ewm(span=slow_period).mean()
            
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=signal_period).mean()
            histogram = macd - signal
            
            return {
                'macd': macd,
                'signal': signal,
                'histogram': histogram
            }
            
        except Exception as e:
            logger.error(f"计算MACD失败: {str(e)}")
            return {
                'macd': pd.Series(index=prices.index, dtype=float),
                'signal': pd.Series(index=prices.index, dtype=float),
                'histogram': pd.Series(index=prices.index, dtype=float)
            }
    
    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2
    ) -> Dict[str, pd.Series]:
        """计算布林带"""
        try:
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
            
        except Exception as e:
            logger.error(f"计算布林带失败: {str(e)}")
            return {
                'upper': pd.Series(index=prices.index, dtype=float),
                'middle': pd.Series(index=prices.index, dtype=float),
                'lower': pd.Series(index=prices.index, dtype=float)
            }
    
    def calculate_confidence_score(
        self,
        conditions: Dict[str, bool],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """计算置信度分数
        
        Args:
            conditions: 条件字典
            weights: 权重字典
            
        Returns:
            置信度分数 (0-100)
        """
        try:
            if not conditions:
                return 0.0
            
            if weights is None:
                # 默认等权重
                weights = {key: 1.0 for key in conditions.keys()}
            
            total_weight = sum(weights.values())
            weighted_score = sum(
                weights.get(key, 0) * (1 if value else 0)
                for key, value in conditions.items()
            )
            
            confidence = (weighted_score / total_weight) * 100
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"计算置信度失败: {str(e)}")
            return 0.0
    
    def format_signal(
        self,
        stock_code: str,
        signal_type: str,
        price: float,
        confidence: float,
        conditions: Dict[str, Any],
        indicators: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """格式化交易信号
        
        Args:
            stock_code: 股票代码
            signal_type: 信号类型 (buy/sell)
            price: 价格
            confidence: 置信度
            conditions: 触发条件
            indicators: 技术指标
            timestamp: 时间戳
            
        Returns:
            格式化的信号字典
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        return {
            'strategy_name': self.name,
            'stock_code': stock_code,
            'signal_type': signal_type,
            'price': price,
            'confidence': confidence,
            'conditions': conditions,
            'indicators': indicators,
            'timestamp': timestamp,
            'risk_management': self.get_risk_management_rules()
        }
    
    def log_signal(self, signal: Dict[str, Any]):
        """记录交易信号"""
        logger.info(
            f"生成信号 - 策略: {signal['strategy_name']}, "
            f"股票: {signal['stock_code']}, "
            f"类型: {signal['signal_type']}, "
            f"价格: {signal['price']}, "
            f"置信度: {signal['confidence']}%"
        )
    
    async def backtest(
        self,
        historical_data: Dict[str, pd.DataFrame],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        """策略回测
        
        Args:
            historical_data: 历史数据字典 {stock_code: DataFrame}
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            
        Returns:
            回测结果
        """
        try:
            logger.info(f"开始回测策略: {self.name}")
            
            # TODO: 实现完整的回测逻辑
            # 这里返回模拟结果
            backtest_result = {
                'strategy_name': self.name,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_capital': initial_capital * 1.1,  # 模拟10%收益
                'total_return': 10.0,
                'max_drawdown': -5.0,
                'sharpe_ratio': 1.2,
                'win_rate': 60.0,
                'total_trades': 20,
                'winning_trades': 12,
                'losing_trades': 8
            }
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"策略回测失败: {str(e)}")
            raise
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            'name': self.name,
            'config': self.config,
            'risk_management': self.get_risk_management_rules(),
            'description': self.__doc__ or f"{self.name} 策略"
        }