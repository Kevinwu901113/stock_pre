#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML模型模块
实现XGBoost等机器学习模型的训练与预测接口
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLModel:
    """
    机器学习模型类，支持多种回归模型的训练与预测
    """
    
    def __init__(self, model_type: str = 'xgboost', model_params: Optional[Dict] = None):
        """
        初始化ML模型
        
        Args:
            model_type: 模型类型，支持'xgboost', 'random_forest', 'gbdt', 'linear', 'ridge', 'lasso', 'svr'
            model_params: 模型参数字典
        """
        self.model_type = model_type
        self.model_params = model_params or {}
        self.model = None
        self.feature_names = None
        self.feature_importance = None
        self.eval_metrics = {}
        
        # 初始化模型
        self._init_model()
    
    def _init_model(self):
        """
        根据模型类型初始化模型
        """
        if self.model_type == 'xgboost':
            default_params = {
                'objective': 'reg:squarederror',
                'learning_rate': 0.1,
                'max_depth': 6,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'gamma': 0,
                'reg_alpha': 0,
                'reg_lambda': 1,
                'random_state': 42
            }
            # 更新默认参数
            params = {**default_params, **self.model_params}
            self.model = xgb.XGBRegressor(**params)
            
        elif self.model_type == 'random_forest':
            default_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2,
                'min_samples_leaf': 1,
                'random_state': 42
            }
            params = {**default_params, **self.model_params}
            self.model = RandomForestRegressor(**params)
            
        elif self.model_type == 'gbdt':
            default_params = {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 3,
                'random_state': 42
            }
            params = {**default_params, **self.model_params}
            self.model = GradientBoostingRegressor(**params)
            
        elif self.model_type == 'linear':
            self.model = LinearRegression(**self.model_params)
            
        elif self.model_type == 'ridge':
            default_params = {'alpha': 1.0, 'random_state': 42}
            params = {**default_params, **self.model_params}
            self.model = Ridge(**params)
            
        elif self.model_type == 'lasso':
            default_params = {'alpha': 0.1, 'random_state': 42}
            params = {**default_params, **self.model_params}
            self.model = Lasso(**params)
            
        elif self.model_type == 'svr':
            default_params = {'kernel': 'rbf', 'C': 1.0, 'epsilon': 0.1}
            params = {**default_params, **self.model_params}
            self.model = SVR(**params)
            
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        logger.info(f"初始化{self.model_type}模型完成")
    
    def train(self, 
             X: Union[pd.DataFrame, np.ndarray], 
             y: Union[pd.Series, np.ndarray],
             eval_set: Optional[Tuple[Union[pd.DataFrame, np.ndarray], Union[pd.Series, np.ndarray]]] = None,
             test_size: float = 0.2,
             time_series_split: bool = True,
             early_stopping_rounds: Optional[int] = None) -> Dict[str, float]:
        """
        训练模型
        
        Args:
            X: 特征数据
            y: 目标变量
            eval_set: 评估数据集
            test_size: 测试集比例
            time_series_split: 是否使用时间序列分割
            early_stopping_rounds: 早停轮数
            
        Returns:
            评估指标字典
        """
        # 保存特征名称
        if isinstance(X, pd.DataFrame):
            self.feature_names = X.columns.tolist()
        
        # 分割训练集和测试集
        if eval_set is None and test_size > 0:
            if time_series_split:
                # 时间序列分割
                train_size = int((1 - test_size) * len(X))
                X_train, X_test = X[:train_size], X[train_size:]
                y_train, y_test = y[:train_size], y[train_size:]
            else:
                # 随机分割
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42
                )
            eval_set = [(X_test, y_test)]
        else:
            X_train, y_train = X, y
        
        # 训练模型
        fit_params = {}
        if self.model_type == 'xgboost' and early_stopping_rounds is not None:
            fit_params = {
                'eval_set': eval_set,
                'early_stopping_rounds': early_stopping_rounds,
                'verbose': False
            }
            self.model.fit(X_train, y_train, **fit_params)
        else:
            self.model.fit(X_train, y_train)
        
        # 计算特征重要性
        self._calculate_feature_importance()
        
        # 评估模型
        if eval_set:
            X_eval, y_eval = eval_set[0]
            metrics = self.evaluate(X_eval, y_eval)
            self.eval_metrics = metrics
            logger.info(f"模型训练完成，评估指标: {metrics}")
            return metrics
        else:
            logger.info("模型训练完成，无评估数据")
            return {}
    
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        模型预测
        
        Args:
            X: 特征数据
            
        Returns:
            预测结果数组
        """
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        return self.model.predict(X)
    
    def evaluate(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """
        评估模型性能
        
        Args:
            X: 特征数据
            y: 真实标签
            
        Returns:
            评估指标字典
        """
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        y_pred = self.predict(X)
        
        metrics = {
            'mse': mean_squared_error(y, y_pred),
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
            'r2': r2_score(y, y_pred)
        }
        
        return metrics
    
    def _calculate_feature_importance(self):
        """
        计算特征重要性
        """
        if self.model is None:
            return
        
        if self.feature_names is None:
            return
        
        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                self.feature_importance = dict(zip(self.feature_names, importances))
            elif self.model_type == 'xgboost':
                # XGBoost特有的特征重要性
                importance_dict = self.model.get_booster().get_score(importance_type='gain')
                self.feature_importance = {}
                for i, name in enumerate(self.feature_names):
                    if name in importance_dict:
                        self.feature_importance[name] = importance_dict[name]
                    else:
                        self.feature_importance[name] = 0
        except Exception as e:
            logger.warning(f"计算特征重要性失败: {str(e)}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性
        
        Returns:
            特征重要性字典
        """
        if self.feature_importance is None:
            return {}
        
        # 按重要性排序
        sorted_importance = dict(sorted(
            self.feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return sorted_importance
    
    def save_model(self, filepath: str):
        """
        保存模型
        
        Args:
            filepath: 模型保存路径
        """
        if self.model is None:
            raise ValueError("模型尚未训练")
        
        # 创建目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存模型
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'eval_metrics': self.eval_metrics
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"模型已保存至: {filepath}")
    
    def load_model(self, filepath: str):
        """
        加载模型
        
        Args:
            filepath: 模型加载路径
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"模型文件不存在: {filepath}")
        
        # 加载模型
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.feature_names = model_data['feature_names']
        self.feature_importance = model_data['feature_importance']
        self.eval_metrics = model_data['eval_metrics']
        
        logger.info(f"模型已从{filepath}加载")
    
    def tune_hyperparameters(self, 
                           X: Union[pd.DataFrame, np.ndarray], 
                           y: Union[pd.Series, np.ndarray],
                           param_grid: Dict[str, List[Any]],
                           cv: int = 5,
                           time_series_cv: bool = True,
                           scoring: str = 'neg_mean_squared_error') -> Dict:
        """
        超参数调优
        
        Args:
            X: 特征数据
            y: 目标变量
            param_grid: 参数网格
            cv: 交叉验证折数
            time_series_cv: 是否使用时间序列交叉验证
            scoring: 评分标准
            
        Returns:
            最佳参数和评分
        """
        # 初始化模型
        self._init_model()
        
        # 设置交叉验证方法
        if time_series_cv:
            cv_method = TimeSeriesSplit(n_splits=cv)
        else:
            cv_method = cv
        
        # 网格搜索
        grid_search = GridSearchCV(
            estimator=self.model,
            param_grid=param_grid,
            cv=cv_method,
            scoring=scoring,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # 更新模型参数
        self.model = grid_search.best_estimator_
        self.model_params.update(grid_search.best_params_)
        
        # 计算特征重要性
        if isinstance(X, pd.DataFrame):
            self.feature_names = X.columns.tolist()
        self._calculate_feature_importance()
        
        result = {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
        
        logger.info(f"超参数调优完成，最佳参数: {result['best_params']}")
        return result


def create_xgboost_model(params: Optional[Dict] = None) -> MLModel:
    """
    创建XGBoost模型
    
    Args:
        params: 模型参数
        
    Returns:
        MLModel实例
    """
    return MLModel(model_type='xgboost', model_params=params)


def create_random_forest_model(params: Optional[Dict] = None) -> MLModel:
    """
    创建随机森林模型
    
    Args:
        params: 模型参数
        
    Returns:
        MLModel实例
    """
    return MLModel(model_type='random_forest', model_params=params)


def create_gbdt_model(params: Optional[Dict] = None) -> MLModel:
    """
    创建GBDT模型
    
    Args:
        params: 模型参数
        
    Returns:
        MLModel实例
    """
    return MLModel(model_type='gbdt', model_params=params)


def create_linear_model(params: Optional[Dict] = None) -> MLModel:
    """
    创建线性回归模型
    
    Args:
        params: 模型参数
        
    Returns:
        MLModel实例
    """
    return MLModel(model_type='linear', model_params=params)

def create_model(model_type: str = 'xgboost', params: Optional[Dict] = None) -> MLModel:
    """
    创建ML模型的通用函数
    
    Args:
        model_type: 模型类型
        params: 模型参数
        
    Returns:
        MLModel实例
    """
    return MLModel(model_type=model_type, model_params=params)