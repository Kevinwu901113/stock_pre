#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model模块
提供机器学习模型、规则打分模型和预测器接口
"""

from .ml_model import (
    MLModel, 
    create_xgboost_model, 
    create_random_forest_model, 
    create_gbdt_model, 
    create_linear_model
)

from .scorer import (
    RuleScorer, 
    MultiFactorScorer, 
    create_rule_scorer, 
    create_multi_factor_scorer
)

from .predictor import (
    BasePredictor,
    MLPredictor, 
    RulePredictor, 
    EnsemblePredictor, 
    create_ml_predictor, 
    create_rule_predictor, 
    create_ensemble_predictor
)

__all__ = [
    # ML模型
    'MLModel',
    'create_xgboost_model',
    'create_random_forest_model',
    'create_gbdt_model',
    'create_linear_model',
    
    # 规则打分模型
    'RuleScorer',
    'MultiFactorScorer',
    'create_rule_scorer',
    'create_multi_factor_scorer',
    
    # 预测器
    'BasePredictor',
    'MLPredictor',
    'RulePredictor',
    'EnsemblePredictor',
    'create_ml_predictor',
    'create_rule_predictor',
    'create_ensemble_predictor'
]

__version__ = '1.0.0'