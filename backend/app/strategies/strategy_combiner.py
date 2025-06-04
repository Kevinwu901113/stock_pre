#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略组合管理器
支持多个策略的组合执行与过滤机制
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.logging import get_logger
from ..models.strategy import StrategySignal
from .base_strategy import BaseStrategy
from .evening_buy_strategy import EveningBuyStrategy
from .morning_sell_strategy import MorningSellStrategy

logger = get_logger(__name__)


class CombineMethod(str, Enum):
    """策略组合方法"""
    UNION = "union"           # 并集：任一策略触发即生成信号
    INTERSECTION = "intersection"  # 交集：所有策略都触发才生成信号
    WEIGHTED = "weighted"     # 加权：根据权重组合策略信号
    CONSENSUS = "consensus"   # 共识：大多数策略同意才生成信号
    SEQUENTIAL = "sequential" # 顺序：按顺序执行策略


class FilterType(str, Enum):
    """过滤器类型"""
    MARKET_CAP = "market_cap"         # 市值过滤
    TURNOVER_RATE = "turnover_rate"   # 换手率过滤
    VOLUME = "volume"                 # 成交量过滤
    PRICE_RANGE = "price_range"       # 价格区间过滤
    INDUSTRY = "industry"             # 行业过滤
    PE_RATIO = "pe_ratio"             # 市盈率过滤
    PB_RATIO = "pb_ratio"             # 市净率过滤
    ROE = "roe"                       # ROE过滤
    DEBT_RATIO = "debt_ratio"         # 负债率过滤
    GROWTH_RATE = "growth_rate"       # 增长率过滤


@dataclass
class FilterConfig:
    """过滤器配置"""
    filter_type: FilterType
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    include_values: Optional[List[Any]] = None
    exclude_values: Optional[List[Any]] = None
    enabled: bool = True
    weight: float = 1.0


@dataclass
class StrategyWeight:
    """策略权重配置"""
    strategy_name: str
    weight: float
    enabled: bool = True
    min_confidence: float = 0.0


class StrategyCombiner:
    """策略组合管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化策略组合管理器"""
        self.config = config or {}
        self.strategies = {}
        self.filters = []
        self.strategy_weights = []
        self.combine_method = CombineMethod.WEIGHTED
        
        # 初始化默认配置
        self._initialize_default_config()
        
        # 注册策略
        self._register_strategies()
        
        logger.info("策略组合管理器初始化完成")
    
    def _initialize_default_config(self):
        """初始化默认配置"""
        default_config = {
            'combine_method': 'weighted',
            'min_combined_confidence': 60.0,
            'max_signals_per_run': 20,
            'risk_management': {
                'max_position_per_stock': 0.05,  # 单股最大仓位
                'max_total_position': 0.8,       # 总仓位上限
                'sector_concentration_limit': 0.3, # 行业集中度限制
                'correlation_threshold': 0.7      # 相关性阈值
            },
            'filters': {
                'market_cap': {'min_value': 50, 'max_value': None},  # 亿元
                'turnover_rate': {'min_value': 0.5, 'max_value': 15.0},  # %
                'price_range': {'min_value': 5.0, 'max_value': 200.0},  # 元
                'pe_ratio': {'min_value': 5.0, 'max_value': 50.0},
                'pb_ratio': {'min_value': 0.5, 'max_value': 10.0}
            },
            'strategy_weights': {
                'evening_buy': {'weight': 0.6, 'min_confidence': 50.0},
                'morning_sell': {'weight': 0.4, 'min_confidence': 60.0}
            }
        }
        
        # 更新配置
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        # 设置组合方法
        self.combine_method = CombineMethod(self.config['combine_method'])
        
        # 初始化过滤器
        self._initialize_filters()
        
        # 初始化策略权重
        self._initialize_strategy_weights()
    
    def _initialize_filters(self):
        """初始化过滤器"""
        filter_configs = self.config.get('filters', {})
        
        for filter_name, filter_config in filter_configs.items():
            if filter_name in FilterType.__members__.values():
                filter_obj = FilterConfig(
                    filter_type=FilterType(filter_name),
                    min_value=filter_config.get('min_value'),
                    max_value=filter_config.get('max_value'),
                    include_values=filter_config.get('include_values'),
                    exclude_values=filter_config.get('exclude_values'),
                    enabled=filter_config.get('enabled', True),
                    weight=filter_config.get('weight', 1.0)
                )
                self.filters.append(filter_obj)
    
    def _initialize_strategy_weights(self):
        """初始化策略权重"""
        weight_configs = self.config.get('strategy_weights', {})
        
        for strategy_name, weight_config in weight_configs.items():
            weight_obj = StrategyWeight(
                strategy_name=strategy_name,
                weight=weight_config.get('weight', 1.0),
                enabled=weight_config.get('enabled', True),
                min_confidence=weight_config.get('min_confidence', 0.0)
            )
            self.strategy_weights.append(weight_obj)
    
    def _register_strategies(self):
        """注册策略实例"""
        try:
            # 注册尾盘买入策略
            evening_config = self.config.get('strategy_configs', {}).get('evening_buy', {})
            self.strategies['evening_buy'] = EveningBuyStrategy(evening_config)
            
            # 注册早盘卖出策略
            morning_config = self.config.get('strategy_configs', {}).get('morning_sell', {})
            self.strategies['morning_sell'] = MorningSellStrategy(morning_config)
            
            logger.info(f"注册了 {len(self.strategies)} 个策略")
            
        except Exception as e:
            logger.error(f"注册策略失败: {str(e)}")
            raise
    
    async def run_combined_strategy(
        self,
        stock_data_dict: Dict[str, pd.DataFrame],
        strategy_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """运行组合策略
        
        Args:
            stock_data_dict: 股票数据字典 {stock_code: DataFrame}
            strategy_names: 要运行的策略名称列表
            
        Returns:
            组合后的信号列表
        """
        try:
            logger.info(f"运行组合策略，股票数量: {len(stock_data_dict)}")
            
            # 确定要运行的策略
            if not strategy_names:
                strategy_names = list(self.strategies.keys())
            
            # 收集所有策略信号
            all_signals = {}
            
            for strategy_name in strategy_names:
                if strategy_name not in self.strategies:
                    logger.warning(f"策略不存在: {strategy_name}")
                    continue
                
                strategy = self.strategies[strategy_name]
                strategy_signals = []
                
                # 为每个股票生成信号
                for stock_code, stock_data in stock_data_dict.items():
                    try:
                        signals = await strategy.generate_signals(stock_data, stock_code)
                        strategy_signals.extend(signals)
                    except Exception as e:
                        logger.warning(f"策略 {strategy_name} 处理股票 {stock_code} 失败: {str(e)}")
                        continue
                
                all_signals[strategy_name] = strategy_signals
                logger.info(f"策略 {strategy_name} 生成 {len(strategy_signals)} 个信号")
            
            # 应用过滤器
            filtered_signals = await self._apply_filters(all_signals, stock_data_dict)
            
            # 组合策略信号
            combined_signals = await self._combine_signals(filtered_signals)
            
            # 应用风险管理
            final_signals = await self._apply_risk_management(combined_signals)
            
            logger.info(f"组合策略完成，最终生成 {len(final_signals)} 个信号")
            return final_signals
            
        except Exception as e:
            logger.error(f"运行组合策略失败: {str(e)}")
            raise
    
    async def _apply_filters(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]],
        stock_data_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """应用过滤器"""
        try:
            filtered_signals = {}
            
            for strategy_name, signals in signals_dict.items():
                filtered_list = []
                
                for signal in signals:
                    stock_code = signal['stock_code']
                    
                    # 获取股票数据
                    stock_data = stock_data_dict.get(stock_code)
                    if stock_data is None or stock_data.empty:
                        continue
                    
                    # 应用所有过滤器
                    if await self._pass_filters(signal, stock_data):
                        filtered_list.append(signal)
                
                filtered_signals[strategy_name] = filtered_list
                logger.info(f"策略 {strategy_name} 过滤后剩余 {len(filtered_list)} 个信号")
            
            return filtered_signals
            
        except Exception as e:
            logger.error(f"应用过滤器失败: {str(e)}")
            return signals_dict
    
    async def _pass_filters(
        self,
        signal: Dict[str, Any],
        stock_data: pd.DataFrame
    ) -> bool:
        """检查信号是否通过所有过滤器"""
        try:
            latest_data = stock_data.iloc[-1]
            
            for filter_config in self.filters:
                if not filter_config.enabled:
                    continue
                
                if not await self._apply_single_filter(signal, latest_data, filter_config):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"过滤器检查失败: {str(e)}")
            return False
    
    async def _apply_single_filter(
        self,
        signal: Dict[str, Any],
        stock_data: pd.Series,
        filter_config: FilterConfig
    ) -> bool:
        """应用单个过滤器"""
        try:
            filter_type = filter_config.filter_type
            
            # 获取对应的数据值
            if filter_type == FilterType.MARKET_CAP:
                value = stock_data.get('market_cap', 0) / 100000000  # 转换为亿元
            elif filter_type == FilterType.TURNOVER_RATE:
                value = stock_data.get('turnover_rate', 0)
            elif filter_type == FilterType.VOLUME:
                value = stock_data.get('volume', 0)
            elif filter_type == FilterType.PRICE_RANGE:
                value = stock_data.get('close_price', 0)
            elif filter_type == FilterType.PE_RATIO:
                value = stock_data.get('pe_ratio', 0)
            elif filter_type == FilterType.PB_RATIO:
                value = stock_data.get('pb_ratio', 0)
            else:
                return True  # 未知过滤器类型，默认通过
            
            # 应用数值范围过滤
            if filter_config.min_value is not None and value < filter_config.min_value:
                return False
            
            if filter_config.max_value is not None and value > filter_config.max_value:
                return False
            
            # 应用包含/排除过滤
            if filter_config.include_values and value not in filter_config.include_values:
                return False
            
            if filter_config.exclude_values and value in filter_config.exclude_values:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"应用过滤器失败: {filter_type} - {str(e)}")
            return True
    
    async def _combine_signals(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """组合策略信号"""
        try:
            if self.combine_method == CombineMethod.UNION:
                return await self._combine_union(signals_dict)
            elif self.combine_method == CombineMethod.INTERSECTION:
                return await self._combine_intersection(signals_dict)
            elif self.combine_method == CombineMethod.WEIGHTED:
                return await self._combine_weighted(signals_dict)
            elif self.combine_method == CombineMethod.CONSENSUS:
                return await self._combine_consensus(signals_dict)
            elif self.combine_method == CombineMethod.SEQUENTIAL:
                return await self._combine_sequential(signals_dict)
            else:
                logger.warning(f"未知的组合方法: {self.combine_method}")
                return await self._combine_weighted(signals_dict)
                
        except Exception as e:
            logger.error(f"组合信号失败: {str(e)}")
            return []
    
    async def _combine_weighted(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """加权组合策略信号"""
        try:
            # 按股票代码分组信号
            stock_signals = {}
            
            for strategy_name, signals in signals_dict.items():
                strategy_weight = self._get_strategy_weight(strategy_name)
                
                for signal in signals:
                    stock_code = signal['stock_code']
                    
                    if stock_code not in stock_signals:
                        stock_signals[stock_code] = []
                    
                    # 添加策略权重信息
                    weighted_signal = signal.copy()
                    weighted_signal['strategy_weight'] = strategy_weight.weight
                    weighted_signal['strategy_name'] = strategy_name
                    
                    stock_signals[stock_code].append(weighted_signal)
            
            # 计算加权组合信号
            combined_signals = []
            
            for stock_code, signals in stock_signals.items():
                if not signals:
                    continue
                
                # 计算加权置信度
                total_weight = sum(s['strategy_weight'] for s in signals)
                weighted_confidence = sum(
                    s['confidence'] * s['strategy_weight'] for s in signals
                ) / total_weight if total_weight > 0 else 0
                
                # 检查最小置信度要求
                if weighted_confidence < self.config['min_combined_confidence']:
                    continue
                
                # 创建组合信号
                combined_signal = {
                    'stock_code': stock_code,
                    'signal_type': signals[0]['signal_type'],  # 使用第一个信号的类型
                    'signal_time': datetime.now().isoformat(),
                    'price': signals[0]['price'],
                    'confidence': weighted_confidence,
                    'combined_from': [s['strategy_name'] for s in signals],
                    'strategy_signals': signals,
                    'combination_method': 'weighted'
                }
                
                combined_signals.append(combined_signal)
            
            return combined_signals
            
        except Exception as e:
            logger.error(f"加权组合失败: {str(e)}")
            return []
    
    async def _combine_union(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """并集组合：任一策略触发即生成信号"""
        all_signals = []
        seen_stocks = set()
        
        for strategy_name, signals in signals_dict.items():
            for signal in signals:
                stock_code = signal['stock_code']
                if stock_code not in seen_stocks:
                    signal['combination_method'] = 'union'
                    signal['combined_from'] = [strategy_name]
                    all_signals.append(signal)
                    seen_stocks.add(stock_code)
        
        return all_signals
    
    async def _combine_intersection(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """交集组合：所有策略都触发才生成信号"""
        if not signals_dict:
            return []
        
        # 找到所有策略都推荐的股票
        strategy_stocks = {}
        for strategy_name, signals in signals_dict.items():
            strategy_stocks[strategy_name] = {s['stock_code'] for s in signals}
        
        # 计算交集
        common_stocks = set.intersection(*strategy_stocks.values()) if strategy_stocks else set()
        
        # 生成交集信号
        combined_signals = []
        for stock_code in common_stocks:
            # 找到该股票的所有策略信号
            stock_signals = []
            for strategy_name, signals in signals_dict.items():
                for signal in signals:
                    if signal['stock_code'] == stock_code:
                        stock_signals.append(signal)
                        break
            
            if stock_signals:
                # 使用平均置信度
                avg_confidence = sum(s['confidence'] for s in stock_signals) / len(stock_signals)
                
                combined_signal = {
                    'stock_code': stock_code,
                    'signal_type': stock_signals[0]['signal_type'],
                    'signal_time': datetime.now().isoformat(),
                    'price': stock_signals[0]['price'],
                    'confidence': avg_confidence,
                    'combined_from': list(signals_dict.keys()),
                    'strategy_signals': stock_signals,
                    'combination_method': 'intersection'
                }
                
                combined_signals.append(combined_signal)
        
        return combined_signals
    
    async def _combine_consensus(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """共识组合：大多数策略同意才生成信号"""
        # 按股票分组
        stock_signals = {}
        for strategy_name, signals in signals_dict.items():
            for signal in signals:
                stock_code = signal['stock_code']
                if stock_code not in stock_signals:
                    stock_signals[stock_code] = []
                stock_signals[stock_code].append(signal)
        
        # 计算共识阈值（超过一半的策略同意）
        consensus_threshold = len(signals_dict) / 2
        
        combined_signals = []
        for stock_code, signals in stock_signals.items():
            if len(signals) > consensus_threshold:
                avg_confidence = sum(s['confidence'] for s in signals) / len(signals)
                
                combined_signal = {
                    'stock_code': stock_code,
                    'signal_type': signals[0]['signal_type'],
                    'signal_time': datetime.now().isoformat(),
                    'price': signals[0]['price'],
                    'confidence': avg_confidence,
                    'combined_from': [s.get('strategy_name', 'unknown') for s in signals],
                    'strategy_signals': signals,
                    'combination_method': 'consensus'
                }
                
                combined_signals.append(combined_signal)
        
        return combined_signals
    
    async def _combine_sequential(
        self,
        signals_dict: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """顺序组合：按策略权重顺序执行"""
        # 按权重排序策略
        sorted_strategies = sorted(
            self.strategy_weights,
            key=lambda x: x.weight,
            reverse=True
        )
        
        combined_signals = []
        used_stocks = set()
        
        for strategy_weight in sorted_strategies:
            strategy_name = strategy_weight.strategy_name
            if strategy_name not in signals_dict:
                continue
            
            for signal in signals_dict[strategy_name]:
                stock_code = signal['stock_code']
                if stock_code not in used_stocks:
                    signal['combination_method'] = 'sequential'
                    signal['combined_from'] = [strategy_name]
                    combined_signals.append(signal)
                    used_stocks.add(stock_code)
        
        return combined_signals
    
    async def _apply_risk_management(
        self,
        signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """应用风险管理规则"""
        try:
            risk_config = self.config.get('risk_management', {})
            
            # 按置信度排序
            sorted_signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)
            
            # 限制信号数量
            max_signals = self.config.get('max_signals_per_run', 20)
            if len(sorted_signals) > max_signals:
                sorted_signals = sorted_signals[:max_signals]
                logger.info(f"限制信号数量为 {max_signals} 个")
            
            # TODO: 实现更多风险管理规则
            # - 行业集中度控制
            # - 相关性控制
            # - 仓位控制
            
            return sorted_signals
            
        except Exception as e:
            logger.error(f"应用风险管理失败: {str(e)}")
            return signals
    
    def _get_strategy_weight(self, strategy_name: str) -> StrategyWeight:
        """获取策略权重配置"""
        for weight in self.strategy_weights:
            if weight.strategy_name == strategy_name:
                return weight
        
        # 返回默认权重
        return StrategyWeight(strategy_name=strategy_name, weight=1.0)
    
    def add_strategy(self, strategy_name: str, strategy: BaseStrategy, weight: float = 1.0):
        """添加新策略"""
        self.strategies[strategy_name] = strategy
        
        # 添加权重配置
        weight_obj = StrategyWeight(
            strategy_name=strategy_name,
            weight=weight,
            enabled=True
        )
        self.strategy_weights.append(weight_obj)
        
        logger.info(f"添加策略: {strategy_name}, 权重: {weight}")
    
    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            
            # 移除权重配置
            self.strategy_weights = [
                w for w in self.strategy_weights 
                if w.strategy_name != strategy_name
            ]
            
            logger.info(f"移除策略: {strategy_name}")
    
    def add_filter(self, filter_config: FilterConfig):
        """添加过滤器"""
        self.filters.append(filter_config)
        logger.info(f"添加过滤器: {filter_config.filter_type}")
    
    def remove_filter(self, filter_type: FilterType):
        """移除过滤器"""
        self.filters = [f for f in self.filters if f.filter_type != filter_type]
        logger.info(f"移除过滤器: {filter_type}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'combine_method': self.combine_method.value,
            'strategies': list(self.strategies.keys()),
            'filters': [{
                'type': f.filter_type.value,
                'min_value': f.min_value,
                'max_value': f.max_value,
                'enabled': f.enabled
            } for f in self.filters],
            'strategy_weights': [{
                'strategy_name': w.strategy_name,
                'weight': w.weight,
                'enabled': w.enabled
            } for w in self.strategy_weights],
            'risk_management': self.config.get('risk_management', {})
        }