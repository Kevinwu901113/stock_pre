#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则打分模型模块
提供基于多个因子线性加权的打分模型
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
import json
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleScorer:
    """
    规则打分模型，支持基于多个因子线性加权得分
    """
    
    def __init__(self, factor_weights: Optional[Dict[str, float]] = None):
        """
        初始化规则打分模型
        
        Args:
            factor_weights: 因子权重字典，格式为 {因子名称: 权重}
        """
        self.factor_weights = factor_weights or {}
        self.factor_directions = {}  # 因子方向，1表示因子值越大越好，-1表示因子值越小越好
        self.factor_ranges = {}  # 因子取值范围，用于归一化
        self.score_range = (0, 100)  # 分数范围
    
    def set_factor_weights(self, factor_weights: Dict[str, float]):
        """
        设置因子权重
        
        Args:
            factor_weights: 因子权重字典
        """
        self.factor_weights = factor_weights
        logger.info(f"设置因子权重: {factor_weights}")
    
    def set_factor_directions(self, factor_directions: Dict[str, int]):
        """
        设置因子方向
        
        Args:
            factor_directions: 因子方向字典，1表示因子值越大越好，-1表示因子值越小越好
        """
        self.factor_directions = factor_directions
        logger.info(f"设置因子方向: {factor_directions}")
    
    def set_factor_ranges(self, factor_ranges: Dict[str, Tuple[float, float]]):
        """
        设置因子取值范围
        
        Args:
            factor_ranges: 因子取值范围字典，格式为 {因子名称: (最小值, 最大值)}
        """
        self.factor_ranges = factor_ranges
        logger.info(f"设置因子取值范围: {factor_ranges}")
    
    def set_score_range(self, min_score: float, max_score: float):
        """
        设置分数范围
        
        Args:
            min_score: 最小分数
            max_score: 最大分数
        """
        self.score_range = (min_score, max_score)
        logger.info(f"设置分数范围: {self.score_range}")
    
    def normalize_factor(self, factor_name: str, factor_values: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """
        归一化因子值
        
        Args:
            factor_name: 因子名称
            factor_values: 因子值
            
        Returns:
            归一化后的因子值
        """
        # 获取因子范围
        if factor_name in self.factor_ranges:
            min_val, max_val = self.factor_ranges[factor_name]
        else:
            min_val, max_val = np.nanmin(factor_values), np.nanmax(factor_values)
            self.factor_ranges[factor_name] = (min_val, max_val)
        
        # 避免除以零
        if max_val == min_val:
            return np.zeros_like(factor_values)
        
        # 归一化到[0,1]区间
        normalized = (factor_values - min_val) / (max_val - min_val)
        
        # 根据因子方向调整
        if factor_name in self.factor_directions and self.factor_directions[factor_name] == -1:
            normalized = 1 - normalized
        
        return normalized
    
    def calculate_score(self, data: pd.DataFrame) -> pd.Series:
        """
        计算综合得分
        
        Args:
            data: 包含因子值的DataFrame
            
        Returns:
            综合得分Series
        """
        if not self.factor_weights:
            raise ValueError("因子权重未设置")
        
        # 检查数据中是否包含所有需要的因子
        missing_factors = [f for f in self.factor_weights.keys() if f not in data.columns]
        if missing_factors:
            logger.warning(f"数据中缺少以下因子: {missing_factors}")
        
        # 计算每个因子的得分贡献
        factor_scores = pd.DataFrame(index=data.index)
        total_weight = 0
        
        for factor, weight in self.factor_weights.items():
            if factor in data.columns:
                # 归一化因子值
                normalized_values = self.normalize_factor(factor, data[factor])
                
                # 计算因子得分贡献
                factor_scores[factor] = normalized_values * weight
                total_weight += weight
        
        # 计算综合得分
        if total_weight > 0:
            # 归一化权重
            for factor in factor_scores.columns:
                factor_scores[factor] = factor_scores[factor] * (self.factor_weights[factor] / total_weight)
            
            # 求和得到综合得分
            composite_score = factor_scores.sum(axis=1)
            
            # 调整到指定分数范围
            min_score, max_score = self.score_range
            adjusted_score = composite_score * (max_score - min_score) + min_score
            
            return adjusted_score
        else:
            return pd.Series(np.nan, index=data.index)
    
    def rank_stocks(self, data: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
        """
        对股票进行排名
        
        Args:
            data: 包含因子值的DataFrame，必须包含'symbol'列
            ascending: 是否按分数升序排序
            
        Returns:
            包含股票代码、得分和排名的DataFrame
        """
        if 'symbol' not in data.columns:
            raise ValueError("数据必须包含'symbol'列")
        
        # 计算得分
        scores = self.calculate_score(data)
        
        # 创建结果DataFrame
        result = pd.DataFrame({
            'symbol': data['symbol'],
            'score': scores
        })
        
        # 排序
        result = result.sort_values('score', ascending=ascending)
        
        # 添加排名
        result['rank'] = range(1, len(result) + 1)
        
        return result
    
    def get_top_stocks(self, data: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        获取得分最高的股票
        
        Args:
            data: 包含因子值的DataFrame，必须包含'symbol'列
            top_n: 返回的股票数量
            
        Returns:
            得分最高的top_n只股票
        """
        ranked = self.rank_stocks(data, ascending=False)
        return ranked.head(top_n)
    
    def get_factor_contribution(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算各因子对得分的贡献
        
        Args:
            data: 包含因子值的DataFrame
            
        Returns:
            各因子得分贡献的DataFrame
        """
        if not self.factor_weights:
            raise ValueError("因子权重未设置")
        
        # 计算每个因子的得分贡献
        factor_scores = pd.DataFrame(index=data.index)
        total_weight = sum(self.factor_weights.values())
        
        for factor, weight in self.factor_weights.items():
            if factor in data.columns:
                # 归一化因子值
                normalized_values = self.normalize_factor(factor, data[factor])
                
                # 计算因子得分贡献
                normalized_weight = weight / total_weight
                min_score, max_score = self.score_range
                factor_scores[factor] = normalized_values * normalized_weight * (max_score - min_score) + min_score * normalized_weight
        
        # 添加总分
        factor_scores['total_score'] = factor_scores.sum(axis=1)
        
        return factor_scores
    
    def save_model(self, filepath: str):
        """
        保存模型配置
        
        Args:
            filepath: 保存路径
        """
        model_config = {
            'factor_weights': self.factor_weights,
            'factor_directions': self.factor_directions,
            'factor_ranges': {k: list(v) for k, v in self.factor_ranges.items()},
            'score_range': list(self.score_range)
        }
        
        # 创建目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存配置
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, indent=4)
        
        logger.info(f"模型配置已保存至: {filepath}")
    
    def load_model(self, filepath: str):
        """
        加载模型配置
        
        Args:
            filepath: 配置文件路径
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
        
        # 加载配置
        with open(filepath, 'r', encoding='utf-8') as f:
            model_config = json.load(f)
        
        self.factor_weights = model_config['factor_weights']
        self.factor_directions = model_config['factor_directions']
        self.factor_ranges = {k: tuple(v) for k, v in model_config['factor_ranges'].items()}
        self.score_range = tuple(model_config['score_range'])
        
        logger.info(f"模型配置已从{filepath}加载")


class MultiFactorScorer(RuleScorer):
    """
    多因子打分模型，扩展了RuleScorer的功能
    """
    
    def __init__(self, factor_groups: Optional[Dict[str, Dict[str, float]]] = None):
        """
        初始化多因子打分模型
        
        Args:
            factor_groups: 因子组权重字典，格式为 {组名: {因子名: 权重}}
        """
        super().__init__()
        self.factor_groups = factor_groups or {}
        self.group_weights = {}  # 组权重
    
    def set_factor_groups(self, factor_groups: Dict[str, Dict[str, float]]):
        """
        设置因子组
        
        Args:
            factor_groups: 因子组权重字典
        """
        self.factor_groups = factor_groups
        
        # 更新因子权重
        self._update_factor_weights()
        
        logger.info(f"设置因子组: {list(factor_groups.keys())}")
    
    def set_group_weights(self, group_weights: Dict[str, float]):
        """
        设置组权重
        
        Args:
            group_weights: 组权重字典
        """
        self.group_weights = group_weights
        
        # 更新因子权重
        self._update_factor_weights()
        
        logger.info(f"设置组权重: {group_weights}")
    
    def _update_factor_weights(self):
        """
        根据因子组和组权重更新因子权重
        """
        factor_weights = {}
        
        # 如果没有设置组权重，则默认每组权重相等
        if not self.group_weights and self.factor_groups:
            self.group_weights = {group: 1.0 for group in self.factor_groups}
        
        # 计算每个因子的权重
        for group, factors in self.factor_groups.items():
            if group in self.group_weights:
                group_weight = self.group_weights[group]
                
                # 计算组内每个因子的权重
                for factor, factor_weight in factors.items():
                    factor_weights[factor] = factor_weight * group_weight
        
        self.factor_weights = factor_weights
    
    def calculate_group_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算各组的得分
        
        Args:
            data: 包含因子值的DataFrame
            
        Returns:
            各组得分的DataFrame
        """
        group_scores = pd.DataFrame(index=data.index)
        
        for group, factors in self.factor_groups.items():
            # 创建临时RuleScorer计算组内得分
            scorer = RuleScorer(factor_weights=factors)
            scorer.factor_directions = {f: d for f, d in self.factor_directions.items() if f in factors}
            scorer.factor_ranges = {f: r for f, r in self.factor_ranges.items() if f in factors}
            
            # 计算组得分
            group_scores[group] = scorer.calculate_score(data)
        
        # 添加总分
        if self.group_weights:
            total_score = pd.Series(0, index=data.index)
            total_weight = sum(self.group_weights.values())
            
            for group, weight in self.group_weights.items():
                if group in group_scores.columns:
                    normalized_weight = weight / total_weight
                    total_score += group_scores[group] * normalized_weight
            
            group_scores['total_score'] = total_score
        
        return group_scores
    
    def save_model(self, filepath: str):
        """
        保存模型配置
        
        Args:
            filepath: 保存路径
        """
        model_config = {
            'factor_groups': self.factor_groups,
            'group_weights': self.group_weights,
            'factor_directions': self.factor_directions,
            'factor_ranges': {k: list(v) for k, v in self.factor_ranges.items()},
            'score_range': list(self.score_range)
        }
        
        # 创建目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存配置
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, indent=4)
        
        logger.info(f"多因子模型配置已保存至: {filepath}")
    
    def load_model(self, filepath: str):
        """
        加载模型配置
        
        Args:
            filepath: 配置文件路径
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
        
        # 加载配置
        with open(filepath, 'r', encoding='utf-8') as f:
            model_config = json.load(f)
        
        self.factor_groups = model_config['factor_groups']
        self.group_weights = model_config['group_weights']
        self.factor_directions = model_config['factor_directions']
        self.factor_ranges = {k: tuple(v) for k, v in model_config['factor_ranges'].items()}
        self.score_range = tuple(model_config['score_range'])
        
        # 更新因子权重
        self._update_factor_weights()
        
        logger.info(f"多因子模型配置已从{filepath}加载")


def create_rule_scorer(factor_weights: Optional[Dict[str, float]] = None) -> RuleScorer:
    """
    创建规则打分模型
    
    Args:
        factor_weights: 因子权重字典
        
    Returns:
        RuleScorer实例
    """
    return RuleScorer(factor_weights=factor_weights)


def create_multi_factor_scorer(factor_groups: Optional[Dict[str, Dict[str, float]]] = None) -> MultiFactorScorer:
    """
    创建多因子打分模型
    
    Args:
        factor_groups: 因子组权重字典
        
    Returns:
        MultiFactorScorer实例
    """
    return MultiFactorScorer(factor_groups=factor_groups)