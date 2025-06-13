#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预测器模块
统一封装模型推理接口，对外暴露统一predict方法
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import os
import logging
import json
from abc import ABC, abstractmethod

# 导入模型模块
from .ml_model import MLModel
from .scorer import RuleScorer, MultiFactorScorer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BasePredictor(ABC):
    """
    预测器基类，定义通用接口
    """
    
    def __init__(self, name: str = 'base_predictor'):
        """
        初始化预测器
        
        Args:
            name: 预测器名称
        """
        self.name = name
        self.metadata = {}
    
    @abstractmethod
    def predict(self, data: pd.DataFrame) -> pd.Series:
        """
        预测方法
        
        Args:
            data: 输入数据
            
        Returns:
            预测结果
        """
        pass
    
    @abstractmethod
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """
        评估方法
        
        Args:
            data: 输入数据
            target: 目标变量
            
        Returns:
            评估指标
        """
        pass
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """
        设置元数据
        
        Args:
            metadata: 元数据字典
        """
        self.metadata = metadata
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取元数据
        
        Returns:
            元数据字典
        """
        return self.metadata


class MLPredictor(BasePredictor):
    """
    机器学习模型预测器
    """
    
    def __init__(self, model: Optional[MLModel] = None, name: str = 'ml_predictor'):
        """
        初始化ML预测器
        
        Args:
            model: MLModel实例
            name: 预测器名称
        """
        super().__init__(name=name)
        self.model = model
        self.feature_columns = []  # 特征列名
        self.target_column = None  # 目标列名
        self.preprocessing_steps = []  # 预处理步骤
        self.postprocessing_steps = []  # 后处理步骤
    
    def set_model(self, model: MLModel):
        """
        设置模型
        
        Args:
            model: MLModel实例
        """
        self.model = model
    
    def set_feature_columns(self, feature_columns: List[str]):
        """
        设置特征列名
        
        Args:
            feature_columns: 特征列名列表
        """
        self.feature_columns = feature_columns
    
    def set_target_column(self, target_column: str):
        """
        设置目标列名
        
        Args:
            target_column: 目标列名
        """
        self.target_column = target_column
    
    def add_preprocessing_step(self, step: Callable[[pd.DataFrame], pd.DataFrame]):
        """
        添加预处理步骤
        
        Args:
            step: 预处理函数，接收DataFrame并返回处理后的DataFrame
        """
        self.preprocessing_steps.append(step)
    
    def add_postprocessing_step(self, step: Callable[[pd.Series], pd.Series]):
        """
        添加后处理步骤
        
        Args:
            step: 后处理函数，接收Series并返回处理后的Series
        """
        self.postprocessing_steps.append(step)
    
    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        执行预处理步骤
        
        Args:
            data: 输入数据
            
        Returns:
            预处理后的数据
        """
        processed_data = data.copy()
        
        # 执行预处理步骤
        for step in self.preprocessing_steps:
            processed_data = step(processed_data)
        
        return processed_data
    
    def postprocess(self, predictions: pd.Series) -> pd.Series:
        """
        执行后处理步骤
        
        Args:
            predictions: 预测结果
            
        Returns:
            后处理后的预测结果
        """
        processed_predictions = predictions.copy()
        
        # 执行后处理步骤
        for step in self.postprocessing_steps:
            processed_predictions = step(processed_predictions)
        
        return processed_predictions
    
    def predict(self, data: pd.DataFrame) -> pd.Series:
        """
        预测方法
        
        Args:
            data: 输入数据
            
        Returns:
            预测结果
        """
        if self.model is None:
            raise ValueError("模型未设置")
        
        # 预处理
        processed_data = self.preprocess(data)
        
        # 提取特征
        if not self.feature_columns:
            # 如果未指定特征列，使用模型的特征名称
            if hasattr(self.model, 'feature_names') and self.model.feature_names:
                features = processed_data[self.model.feature_names]
            else:
                # 排除常见的非特征列
                exclude_cols = ['date', 'symbol', 'code', 'name', 'target']
                if self.target_column:
                    exclude_cols.append(self.target_column)
                features = processed_data.drop(columns=[col for col in exclude_cols if col in processed_data.columns])
        else:
            # 使用指定的特征列
            features = processed_data[self.feature_columns]
        
        # 预测
        predictions = self.model.predict(features)
        
        # 转换为Series
        if isinstance(predictions, np.ndarray):
            predictions = pd.Series(predictions, index=processed_data.index)
        
        # 后处理
        processed_predictions = self.postprocess(predictions)
        
        return processed_predictions
    
    def evaluate(self, data: pd.DataFrame, target: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        评估方法
        
        Args:
            data: 输入数据
            target: 目标变量，如果为None则从data中提取
            
        Returns:
            评估指标
        """
        if self.model is None:
            raise ValueError("模型未设置")
        
        # 预处理
        processed_data = self.preprocess(data)
        
        # 提取目标变量
        if target is None:
            if self.target_column is None:
                raise ValueError("目标列未设置")
            if self.target_column not in processed_data.columns:
                raise ValueError(f"数据中不存在目标列: {self.target_column}")
            target = processed_data[self.target_column]
        
        # 提取特征
        if not self.feature_columns:
            # 如果未指定特征列，使用模型的特征名称
            if hasattr(self.model, 'feature_names') and self.model.feature_names:
                features = processed_data[self.model.feature_names]
            else:
                # 排除常见的非特征列
                exclude_cols = ['date', 'symbol', 'code', 'name', 'target']
                if self.target_column:
                    exclude_cols.append(self.target_column)
                features = processed_data.drop(columns=[col for col in exclude_cols if col in processed_data.columns])
        else:
            # 使用指定的特征列
            features = processed_data[self.feature_columns]
        
        # 评估
        metrics = self.model.evaluate(features, target)
        
        return metrics
    
    def save(self, directory: str):
        """
        保存预测器
        
        Args:
            directory: 保存目录
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # 保存模型
        if self.model is not None:
            self.model.save_model(os.path.join(directory, f"{self.name}_model.pkl"))
        
        # 保存配置
        config = {
            'name': self.name,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'metadata': self.metadata
        }
        
        with open(os.path.join(directory, f"{self.name}_config.json"), 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"预测器已保存至: {directory}")
    
    def load(self, directory: str, model_class=MLModel):
        """
        加载预测器
        
        Args:
            directory: 加载目录
            model_class: 模型类，默认为MLModel
        """
        # 加载配置
        config_path = os.path.join(directory, f"{self.name}_config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.name = config['name']
        self.feature_columns = config['feature_columns']
        self.target_column = config['target_column']
        self.metadata = config['metadata']
        
        # 加载模型
        model_path = os.path.join(directory, f"{self.name}_model.pkl")
        if os.path.exists(model_path):
            self.model = model_class()
            self.model.load_model(model_path)
        
        logger.info(f"预测器已从{directory}加载")


class RulePredictor(BasePredictor):
    """
    规则模型预测器
    """
    
    def __init__(self, scorer: Optional[Union[RuleScorer, MultiFactorScorer]] = None, name: str = 'rule_predictor'):
        """
        初始化规则预测器
        
        Args:
            scorer: 规则打分模型
            name: 预测器名称
        """
        super().__init__(name=name)
        self.scorer = scorer
        self.preprocessing_steps = []  # 预处理步骤
    
    def set_scorer(self, scorer: Union[RuleScorer, MultiFactorScorer]):
        """
        设置打分模型
        
        Args:
            scorer: 规则打分模型
        """
        self.scorer = scorer
    
    def add_preprocessing_step(self, step: Callable[[pd.DataFrame], pd.DataFrame]):
        """
        添加预处理步骤
        
        Args:
            step: 预处理函数，接收DataFrame并返回处理后的DataFrame
        """
        self.preprocessing_steps.append(step)
    
    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        执行预处理步骤
        
        Args:
            data: 输入数据
            
        Returns:
            预处理后的数据
        """
        processed_data = data.copy()
        
        # 执行预处理步骤
        for step in self.preprocessing_steps:
            processed_data = step(processed_data)
        
        return processed_data
    
    def predict(self, data: pd.DataFrame) -> pd.Series:
        """
        预测方法
        
        Args:
            data: 输入数据
            
        Returns:
            预测结果（得分）
        """
        if self.scorer is None:
            raise ValueError("打分模型未设置")
        
        # 预处理
        processed_data = self.preprocess(data)
        
        # 计算得分
        scores = self.scorer.calculate_score(processed_data)
        
        return scores
    
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """
        评估方法
        
        Args:
            data: 输入数据
            target: 目标变量
            
        Returns:
            评估指标
        """
        # 预测
        predictions = self.predict(data)
        
        # 计算相关系数
        corr = predictions.corr(target)
        rank_corr = predictions.corr(target, method='spearman')
        
        # 计算IC值
        ic = np.corrcoef(predictions.values, target.values)[0, 1]
        
        # 计算排名准确率
        pred_ranks = predictions.rank(ascending=False)
        target_ranks = target.rank(ascending=False)
        rank_diff = np.abs(pred_ranks - target_ranks)
        rank_accuracy = 1 - (rank_diff.mean() / len(predictions))
        
        metrics = {
            'correlation': corr,
            'rank_correlation': rank_corr,
            'ic': ic,
            'rank_accuracy': rank_accuracy
        }
        
        return metrics
    
    def get_factor_contribution(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        获取因子贡献
        
        Args:
            data: 输入数据
            
        Returns:
            因子贡献DataFrame
        """
        if self.scorer is None:
            raise ValueError("打分模型未设置")
        
        # 预处理
        processed_data = self.preprocess(data)
        
        # 获取因子贡献
        if hasattr(self.scorer, 'get_factor_contribution'):
            return self.scorer.get_factor_contribution(processed_data)
        else:
            raise NotImplementedError("打分模型不支持获取因子贡献")
    
    def save(self, directory: str):
        """
        保存预测器
        
        Args:
            directory: 保存目录
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # 保存打分模型
        if self.scorer is not None:
            self.scorer.save_model(os.path.join(directory, f"{self.name}_scorer.json"))
        
        # 保存配置
        config = {
            'name': self.name,
            'metadata': self.metadata
        }
        
        with open(os.path.join(directory, f"{self.name}_config.json"), 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"规则预测器已保存至: {directory}")
    
    def load(self, directory: str, scorer_class=RuleScorer):
        """
        加载预测器
        
        Args:
            directory: 加载目录
            scorer_class: 打分模型类，默认为RuleScorer
        """
        # 加载配置
        config_path = os.path.join(directory, f"{self.name}_config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.name = config['name']
        self.metadata = config['metadata']
        
        # 加载打分模型
        scorer_path = os.path.join(directory, f"{self.name}_scorer.json")
        if os.path.exists(scorer_path):
            self.scorer = scorer_class()
            self.scorer.load_model(scorer_path)
        
        logger.info(f"规则预测器已从{directory}加载")


class EnsemblePredictor(BasePredictor):
    """
    集成预测器，组合多个预测器的结果
    """
    
    def __init__(self, predictors: Optional[List[BasePredictor]] = None, weights: Optional[List[float]] = None, name: str = 'ensemble_predictor'):
        """
        初始化集成预测器
        
        Args:
            predictors: 预测器列表
            weights: 权重列表
            name: 预测器名称
        """
        super().__init__(name=name)
        self.predictors = predictors or []
        self.weights = weights or []
        self.normalize_scores = True  # 是否归一化各预测器的分数
    
    def add_predictor(self, predictor: BasePredictor, weight: float = 1.0):
        """
        添加预测器
        
        Args:
            predictor: 预测器
            weight: 权重
        """
        self.predictors.append(predictor)
        self.weights.append(weight)
    
    def set_weights(self, weights: List[float]):
        """
        设置权重
        
        Args:
            weights: 权重列表
        """
        if len(weights) != len(self.predictors):
            raise ValueError("权重数量与预测器数量不匹配")
        self.weights = weights
    
    def set_normalize_scores(self, normalize: bool):
        """
        设置是否归一化分数
        
        Args:
            normalize: 是否归一化
        """
        self.normalize_scores = normalize
    
    def predict(self, data: pd.DataFrame) -> pd.Series:
        """
        预测方法
        
        Args:
            data: 输入数据
            
        Returns:
            预测结果
        """
        if not self.predictors:
            raise ValueError("未添加预测器")
        
        # 确保权重列表长度与预测器列表长度一致
        if len(self.weights) != len(self.predictors):
            self.weights = [1.0] * len(self.predictors)
        
        # 获取各预测器的预测结果
        predictions = []
        for predictor in self.predictors:
            pred = predictor.predict(data)
            predictions.append(pred)
        
        # 归一化分数
        if self.normalize_scores:
            normalized_predictions = []
            for pred in predictions:
                min_val, max_val = pred.min(), pred.max()
                if max_val > min_val:
                    norm_pred = (pred - min_val) / (max_val - min_val)
                else:
                    norm_pred = pred - min_val  # 避免除以零
                normalized_predictions.append(norm_pred)
            predictions = normalized_predictions
        
        # 加权平均
        total_weight = sum(self.weights)
        if total_weight == 0:
            total_weight = 1.0
        
        ensemble_pred = pd.Series(0, index=data.index)
        for i, pred in enumerate(predictions):
            weight = self.weights[i] / total_weight
            ensemble_pred += pred * weight
        
        return ensemble_pred
    
    def evaluate(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """
        评估方法
        
        Args:
            data: 输入数据
            target: 目标变量
            
        Returns:
            评估指标
        """
        # 预测
        predictions = self.predict(data)
        
        # 计算相关系数
        corr = predictions.corr(target)
        rank_corr = predictions.corr(target, method='spearman')
        
        # 计算IC值
        ic = np.corrcoef(predictions.values, target.values)[0, 1]
        
        # 计算排名准确率
        pred_ranks = predictions.rank(ascending=False)
        target_ranks = target.rank(ascending=False)
        rank_diff = np.abs(pred_ranks - target_ranks)
        rank_accuracy = 1 - (rank_diff.mean() / len(predictions))
        
        # 评估各个预测器
        predictor_metrics = []
        for i, predictor in enumerate(self.predictors):
            metrics = predictor.evaluate(data, target)
            predictor_metrics.append({
                'predictor_name': predictor.name,
                'weight': self.weights[i],
                'metrics': metrics
            })
        
        metrics = {
            'correlation': corr,
            'rank_correlation': rank_corr,
            'ic': ic,
            'rank_accuracy': rank_accuracy,
            'predictor_metrics': predictor_metrics
        }
        
        return metrics
    
    def save(self, directory: str):
        """
        保存预测器
        
        Args:
            directory: 保存目录
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # 保存各个预测器
        predictor_names = []
        for i, predictor in enumerate(self.predictors):
            predictor_dir = os.path.join(directory, f"predictor_{i}")
            os.makedirs(predictor_dir, exist_ok=True)
            predictor.save(predictor_dir)
            predictor_names.append(predictor.name)
        
        # 保存配置
        config = {
            'name': self.name,
            'predictor_names': predictor_names,
            'weights': self.weights,
            'normalize_scores': self.normalize_scores,
            'metadata': self.metadata
        }
        
        with open(os.path.join(directory, f"{self.name}_config.json"), 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"集成预测器已保存至: {directory}")
    
    def load(self, directory: str, predictor_classes: Dict[str, type] = None):
        """
        加载预测器
        
        Args:
            directory: 加载目录
            predictor_classes: 预测器类字典，格式为 {预测器类型: 预测器类}
        """
        # 加载配置
        config_path = os.path.join(directory, f"{self.name}_config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.name = config['name']
        self.weights = config['weights']
        self.normalize_scores = config['normalize_scores']
        self.metadata = config['metadata']
        
        # 加载各个预测器
        self.predictors = []
        for i, predictor_name in enumerate(config['predictor_names']):
            predictor_dir = os.path.join(directory, f"predictor_{i}")
            
            # 确定预测器类型
            predictor_config_path = os.path.join(predictor_dir, f"{predictor_name}_config.json")
            if not os.path.exists(predictor_config_path):
                logger.warning(f"预测器配置不存在: {predictor_config_path}")
                continue
            
            # 根据预测器类型创建预测器
            if predictor_classes is None:
                # 默认使用MLPredictor
                predictor = MLPredictor(name=predictor_name)
            else:
                # 根据配置确定预测器类型
                with open(predictor_config_path, 'r') as f:
                    predictor_type = json.load(f).get('type', 'ml_predictor')
                
                if predictor_type in predictor_classes:
                    predictor = predictor_classes[predictor_type](name=predictor_name)
                else:
                    logger.warning(f"未知的预测器类型: {predictor_type}")
                    continue
            
            # 加载预测器
            predictor.load(predictor_dir)
            self.predictors.append(predictor)
        
        logger.info(f"集成预测器已从{directory}加载")


def create_ml_predictor(model: Optional[MLModel] = None, name: str = 'ml_predictor') -> MLPredictor:
    """
    创建机器学习预测器
    
    Args:
        model: MLModel实例
        name: 预测器名称
        
    Returns:
        MLPredictor实例
    """
    return MLPredictor(model=model, name=name)


def create_rule_predictor(scorer: Optional[Union[RuleScorer, MultiFactorScorer]] = None, name: str = 'rule_predictor') -> RulePredictor:
    """
    创建规则预测器
    
    Args:
        scorer: 规则打分模型
        name: 预测器名称
        
    Returns:
        RulePredictor实例
    """
    return RulePredictor(scorer=scorer, name=name)


def create_ensemble_predictor(predictors: Optional[List[BasePredictor]] = None, weights: Optional[List[float]] = None, name: str = 'ensemble_predictor') -> EnsemblePredictor:
    """
    创建集成预测器
    
    Args:
        predictors: 预测器列表
        weights: 权重列表
        name: 预测器名称
        
    Returns:
        EnsemblePredictor实例
    """
    return EnsemblePredictor(predictors=predictors, weights=weights, name=name)