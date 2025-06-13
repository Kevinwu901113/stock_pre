#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分融合模块

该模块负责融合来自ML模型、规则模型和大模型的评分，
使用可配置的公式输出统一的最终评分，用于推荐排序。
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any
import logging
from abc import ABC, abstractmethod


class FusionStrategy(ABC):
    """评分融合策略抽象基类"""
    
    @abstractmethod
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """融合评分
        
        Args:
            scores: 各模型评分字典 {model_name: score}
            weights: 各模型权重字典 {model_name: weight}
            
        Returns:
            融合后的最终评分
        """
        pass


class WeightedAverageStrategy(FusionStrategy):
    """加权平均融合策略"""
    
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """加权平均融合"""
        total_score = 0.0
        total_weight = 0.0
        
        for model_name, score in scores.items():
            if model_name in weights and score is not None:
                weight = weights[model_name]
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0


class GeometricMeanStrategy(FusionStrategy):
    """几何平均融合策略"""
    
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """几何平均融合"""
        valid_scores = []
        valid_weights = []
        
        for model_name, score in scores.items():
            if model_name in weights and score is not None and score > 0:
                valid_scores.append(score)
                valid_weights.append(weights[model_name])
        
        if not valid_scores:
            return 0.0
        
        # 加权几何平均
        weighted_product = 1.0
        total_weight = sum(valid_weights)
        
        for score, weight in zip(valid_scores, valid_weights):
            normalized_weight = weight / total_weight
            weighted_product *= (score ** normalized_weight)
        
        return weighted_product


class HarmonicMeanStrategy(FusionStrategy):
    """调和平均融合策略"""
    
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """调和平均融合"""
        valid_scores = []
        valid_weights = []
        
        for model_name, score in scores.items():
            if model_name in weights and score is not None and score > 0:
                valid_scores.append(score)
                valid_weights.append(weights[model_name])
        
        if not valid_scores:
            return 0.0
        
        # 加权调和平均
        weighted_reciprocal_sum = 0.0
        total_weight = sum(valid_weights)
        
        for score, weight in zip(valid_scores, valid_weights):
            normalized_weight = weight / total_weight
            weighted_reciprocal_sum += normalized_weight / score
        
        return 1.0 / weighted_reciprocal_sum if weighted_reciprocal_sum > 0 else 0.0


class MaxStrategy(FusionStrategy):
    """最大值融合策略"""
    
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """取最大值"""
        valid_scores = [score for score in scores.values() if score is not None]
        return max(valid_scores) if valid_scores else 0.0


class MinStrategy(FusionStrategy):
    """最小值融合策略"""
    
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """取最小值"""
        valid_scores = [score for score in scores.values() if score is not None]
        return min(valid_scores) if valid_scores else 0.0


class CustomFormulaStrategy(FusionStrategy):
    """自定义公式融合策略"""
    
    def __init__(self, formula_func: Callable[[Dict[str, float], Dict[str, float]], float]):
        """初始化自定义公式策略
        
        Args:
            formula_func: 自定义融合函数，接收scores和weights，返回融合结果
        """
        self.formula_func = formula_func
    
    def fuse(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """使用自定义公式融合"""
        return self.formula_func(scores, weights)


class ScoreFusion:
    """评分融合器
    
    负责融合来自不同模型的评分，支持多种融合策略和可配置参数。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化评分融合器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 默认权重配置
        self.default_weights = {
            'ml_model': 0.4,
            'rule_model': 0.3,
            'llm_model': 0.3
        }
        
        # 融合策略映射
        self.strategies = {
            'weighted_average': WeightedAverageStrategy(),
            'geometric_mean': GeometricMeanStrategy(),
            'harmonic_mean': HarmonicMeanStrategy(),
            'max': MaxStrategy(),
            'min': MinStrategy()
        }
        
        # 当前使用的融合策略
        self.current_strategy = self.config.get('fusion_strategy', 'weighted_average')
        
        # 评分归一化参数
        self.score_range = self.config.get('score_range', (0.0, 1.0))
        self.enable_normalization = self.config.get('enable_normalization', True)
    
    def add_custom_strategy(self, name: str, strategy: FusionStrategy):
        """添加自定义融合策略
        
        Args:
            name: 策略名称
            strategy: 融合策略实例
        """
        self.strategies[name] = strategy
        self.logger.info(f"添加自定义融合策略: {name}")
    
    def set_strategy(self, strategy_name: str):
        """设置融合策略
        
        Args:
            strategy_name: 策略名称
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"未知的融合策略: {strategy_name}")
        
        self.current_strategy = strategy_name
        self.logger.info(f"设置融合策略为: {strategy_name}")
    
    def normalize_score(self, score: float) -> float:
        """归一化评分到指定范围
        
        Args:
            score: 原始评分
            
        Returns:
            归一化后的评分
        """
        if not self.enable_normalization:
            return score
        
        min_score, max_score = self.score_range
        return max(min_score, min(max_score, score))
    
    def validate_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """验证和清理评分数据
        
        Args:
            scores: 原始评分字典
            
        Returns:
            清理后的评分字典
        """
        validated_scores = {}
        
        for model_name, score in scores.items():
            if score is None:
                self.logger.warning(f"模型 {model_name} 的评分为空")
                continue
            
            if not isinstance(score, (int, float)):
                self.logger.warning(f"模型 {model_name} 的评分类型无效: {type(score)}")
                continue
            
            if np.isnan(score) or np.isinf(score):
                self.logger.warning(f"模型 {model_name} 的评分为NaN或无穷大")
                continue
            
            validated_scores[model_name] = float(score)
        
        return validated_scores
    
    def fuse_scores(self, 
                   ml_score: Optional[float] = None,
                   rule_score: Optional[float] = None,
                   llm_score: Optional[float] = None,
                   custom_scores: Optional[Dict[str, float]] = None,
                   weights: Optional[Dict[str, float]] = None) -> float:
        """融合多个模型的评分
        
        Args:
            ml_score: ML模型评分
            rule_score: 规则模型评分
            llm_score: 大模型评分
            custom_scores: 自定义模型评分字典
            weights: 自定义权重字典
            
        Returns:
            融合后的最终评分
        """
        # 构建评分字典
        scores = {}
        if ml_score is not None:
            scores['ml_model'] = ml_score
        if rule_score is not None:
            scores['rule_model'] = rule_score
        if llm_score is not None:
            scores['llm_model'] = llm_score
        
        # 添加自定义评分
        if custom_scores:
            scores.update(custom_scores)
        
        # 验证评分
        scores = self.validate_scores(scores)
        
        if not scores:
            self.logger.warning("没有有效的评分数据")
            return 0.0
        
        # 使用权重
        fusion_weights = weights or self.default_weights
        
        # 确保所有评分都有对应的权重
        for model_name in scores.keys():
            if model_name not in fusion_weights:
                fusion_weights[model_name] = 1.0 / len(scores)
        
        # 获取融合策略
        strategy = self.strategies.get(self.current_strategy)
        if not strategy:
            self.logger.error(f"未找到融合策略: {self.current_strategy}")
            return 0.0
        
        try:
            # 执行融合
            fused_score = strategy.fuse(scores, fusion_weights)
            
            # 归一化结果
            final_score = self.normalize_score(fused_score)
            
            self.logger.debug(f"评分融合完成: {scores} -> {final_score}")
            return final_score
            
        except Exception as e:
            self.logger.error(f"评分融合失败: {e}")
            return 0.0
    
    def batch_fuse_scores(self, 
                         score_list: List[Dict[str, Optional[float]]],
                         weights: Optional[Dict[str, float]] = None) -> List[float]:
        """批量融合评分
        
        Args:
            score_list: 评分列表，每个元素为包含各模型评分的字典
            weights: 权重字典
            
        Returns:
            融合后的评分列表
        """
        results = []
        
        for scores in score_list:
            fused_score = self.fuse_scores(
                ml_score=scores.get('ml_model'),
                rule_score=scores.get('rule_model'),
                llm_score=scores.get('llm_model'),
                custom_scores={k: v for k, v in scores.items() 
                             if k not in ['ml_model', 'rule_model', 'llm_model']},
                weights=weights
            )
            results.append(fused_score)
        
        return results
    
    def get_fusion_info(self) -> Dict[str, Any]:
        """获取融合器信息
        
        Returns:
            融合器配置和状态信息
        """
        return {
            'current_strategy': self.current_strategy,
            'available_strategies': list(self.strategies.keys()),
            'default_weights': self.default_weights,
            'score_range': self.score_range,
            'enable_normalization': self.enable_normalization,
            'config': self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        
        # 更新相关参数
        if 'fusion_strategy' in new_config:
            self.set_strategy(new_config['fusion_strategy'])
        
        if 'score_range' in new_config:
            self.score_range = new_config['score_range']
        
        if 'enable_normalization' in new_config:
            self.enable_normalization = new_config['enable_normalization']
        
        if 'default_weights' in new_config:
            self.default_weights.update(new_config['default_weights'])
        
        self.logger.info("融合器配置已更新")


def create_custom_formula_example():
    """创建自定义公式示例
    
    Returns:
        自定义融合策略实例
    """
    def custom_formula(scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """示例自定义公式：ML模型权重动态调整"""
        ml_score = scores.get('ml_model', 0)
        rule_score = scores.get('rule_model', 0)
        llm_score = scores.get('llm_model', 0)
        
        # 如果ML模型评分很高，增加其权重
        if ml_score > 0.8:
            ml_weight = 0.6
            rule_weight = 0.2
            llm_weight = 0.2
        else:
            ml_weight = weights.get('ml_model', 0.4)
            rule_weight = weights.get('rule_model', 0.3)
            llm_weight = weights.get('llm_model', 0.3)
        
        return (ml_score * ml_weight + 
                rule_score * rule_weight + 
                llm_score * llm_weight)
    
    return CustomFormulaStrategy(custom_formula)


if __name__ == "__main__":
    # 使用示例
    logging.basicConfig(level=logging.INFO)
    
    # 创建融合器
    fusion_config = {
        'fusion_strategy': 'weighted_average',
        'score_range': (0.0, 1.0),
        'enable_normalization': True,
        'default_weights': {
            'ml_model': 0.5,
            'rule_model': 0.3,
            'llm_model': 0.2
        }
    }
    
    fusion = ScoreFusion(fusion_config)
    
    # 融合评分示例
    result = fusion.fuse_scores(
        ml_score=0.85,
        rule_score=0.72,
        llm_score=0.68
    )
    
    print(f"融合结果: {result}")
    
    # 添加自定义策略
    custom_strategy = create_custom_formula_example()
    fusion.add_custom_strategy('custom_dynamic', custom_strategy)
    
    # 使用自定义策略
    fusion.set_strategy('custom_dynamic')
    result2 = fusion.fuse_scores(
        ml_score=0.85,
        rule_score=0.72,
        llm_score=0.68
    )
    
    print(f"自定义策略融合结果: {result2}")
    
    # 批量融合
    score_batch = [
        {'ml_model': 0.8, 'rule_model': 0.7, 'llm_model': 0.6},
        {'ml_model': 0.6, 'rule_model': 0.8, 'llm_model': 0.7},
        {'ml_model': 0.9, 'rule_model': 0.5, 'llm_model': 0.8}
    ]
    
    batch_results = fusion.batch_fuse_scores(score_batch)
    print(f"批量融合结果: {batch_results}")