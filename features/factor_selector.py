#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子选择器模块
负责特征筛选、相关性分析、IC值计算、降维处理
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats
from scipy.stats import spearmanr, pearsonr
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')


class FactorSelector:
    """
    因子选择器类，用于特征筛选和降维处理
    """
    
    def __init__(self):
        self.selected_factors = []
        self.factor_scores = {}
        self.correlation_matrix = None
        self.ic_scores = {}
        self.scaler = StandardScaler()
        self.pca_model = None
        self.factor_analysis_model = None
    
    def calculate_ic_scores(self, 
                           factor_data: pd.DataFrame, 
                           returns: pd.Series,
                           method: str = 'spearman',
                           periods: List[int] = [1, 5, 10, 20]) -> Dict[str, Dict[int, float]]:
        """
        计算因子IC值（信息系数）
        
        Args:
            factor_data: 因子数据DataFrame
            returns: 收益率数据Series
            method: 相关性计算方法，'spearman'或'pearson'
            periods: 计算IC的周期列表
            
        Returns:
            各因子在不同周期的IC值字典
        """
        ic_results = {}
        
        for factor_name in factor_data.columns:
            if factor_name in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']:
                continue
                
            factor_ic = {}
            factor_values = factor_data[factor_name].dropna()
            
            for period in periods:
                # 计算未来period期收益率
                future_returns = returns.shift(-period)
                
                # 对齐数据
                aligned_factor = factor_values.reindex(future_returns.index).dropna()
                aligned_returns = future_returns.reindex(aligned_factor.index).dropna()
                
                if len(aligned_factor) > 10:  # 确保有足够的数据点
                    if method == 'spearman':
                        ic_value, _ = spearmanr(aligned_factor, aligned_returns)
                    else:
                        ic_value, _ = pearsonr(aligned_factor, aligned_returns)
                    
                    factor_ic[period] = ic_value if not np.isnan(ic_value) else 0
                else:
                    factor_ic[period] = 0
            
            ic_results[factor_name] = factor_ic
        
        self.ic_scores = ic_results
        return ic_results
    
    def calculate_ic_ir_scores(self, 
                              factor_data: pd.DataFrame, 
                              returns: pd.Series,
                              window: int = 20) -> Dict[str, Dict[str, float]]:
        """
        计算因子IC和IR值（信息比率）
        
        Args:
            factor_data: 因子数据DataFrame
            returns: 收益率数据Series
            window: 滚动窗口大小
            
        Returns:
            包含IC均值、IC标准差、IR值的字典
        """
        ic_ir_results = {}
        
        for factor_name in factor_data.columns:
            if factor_name in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']:
                continue
            
            factor_values = factor_data[factor_name].dropna()
            future_returns = returns.shift(-1)  # 下期收益率
            
            # 滚动计算IC
            rolling_ic = []
            for i in range(window, len(factor_values)):
                factor_window = factor_values.iloc[i-window:i]
                returns_window = future_returns.iloc[i-window:i]
                
                # 对齐数据
                aligned_data = pd.concat([factor_window, returns_window], axis=1).dropna()
                if len(aligned_data) > 5:
                    ic_value, _ = spearmanr(aligned_data.iloc[:, 0], aligned_data.iloc[:, 1])
                    if not np.isnan(ic_value):
                        rolling_ic.append(ic_value)
            
            if rolling_ic:
                ic_mean = np.mean(rolling_ic)
                ic_std = np.std(rolling_ic)
                ir_value = ic_mean / (ic_std + 1e-8)  # 信息比率
                
                ic_ir_results[factor_name] = {
                    'ic_mean': ic_mean,
                    'ic_std': ic_std,
                    'ir': ir_value,
                    'ic_abs_mean': np.mean(np.abs(rolling_ic))
                }
            else:
                ic_ir_results[factor_name] = {
                    'ic_mean': 0,
                    'ic_std': 0,
                    'ir': 0,
                    'ic_abs_mean': 0
                }
        
        return ic_ir_results
    
    def analyze_factor_correlation(self, 
                                  factor_data: pd.DataFrame,
                                  threshold: float = 0.8) -> Tuple[pd.DataFrame, List[str]]:
        """
        分析因子相关性并识别高相关因子
        
        Args:
            factor_data: 因子数据DataFrame
            threshold: 相关性阈值
            
        Returns:
            相关性矩阵和高相关因子列表
        """
        # 排除非因子列
        factor_cols = [col for col in factor_data.columns 
                      if col not in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']]
        
        factor_subset = factor_data[factor_cols].select_dtypes(include=[np.number])
        
        # 计算相关性矩阵
        correlation_matrix = factor_subset.corr()
        self.correlation_matrix = correlation_matrix
        
        # 识别高相关因子对
        high_corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = abs(correlation_matrix.iloc[i, j])
                if corr_value > threshold:
                    high_corr_pairs.append({
                        'factor1': correlation_matrix.columns[i],
                        'factor2': correlation_matrix.columns[j],
                        'correlation': corr_value
                    })
        
        return correlation_matrix, high_corr_pairs
    
    def remove_highly_correlated_factors(self, 
                                       factor_data: pd.DataFrame,
                                       threshold: float = 0.8,
                                       method: str = 'ic_priority') -> List[str]:
        """
        移除高相关因子
        
        Args:
            factor_data: 因子数据DataFrame
            threshold: 相关性阈值
            method: 选择保留因子的方法，'ic_priority'或'random'
            
        Returns:
            保留的因子列表
        """
        correlation_matrix, high_corr_pairs = self.analyze_factor_correlation(factor_data, threshold)
        
        # 构建因子相关性图
        factor_graph = {}
        for pair in high_corr_pairs:
            factor1, factor2 = pair['factor1'], pair['factor2']
            if factor1 not in factor_graph:
                factor_graph[factor1] = set()
            if factor2 not in factor_graph:
                factor_graph[factor2] = set()
            factor_graph[factor1].add(factor2)
            factor_graph[factor2].add(factor1)
        
        # 选择要移除的因子
        factors_to_remove = set()
        all_factors = set(correlation_matrix.columns)
        
        for factor in all_factors:
            if factor in factors_to_remove:
                continue
            
            if factor in factor_graph:
                correlated_factors = factor_graph[factor]
                
                if method == 'ic_priority' and self.ic_scores:
                    # 基于IC值选择保留因子
                    factor_ic_scores = {}
                    for f in [factor] + list(correlated_factors):
                        if f in self.ic_scores:
                            # 使用IC绝对值的平均值作为评分
                            ic_values = list(self.ic_scores[f].values())
                            factor_ic_scores[f] = np.mean(np.abs(ic_values))
                        else:
                            factor_ic_scores[f] = 0
                    
                    # 保留IC最高的因子
                    best_factor = max(factor_ic_scores.keys(), key=lambda x: factor_ic_scores[x])
                    factors_to_remove.update(correlated_factors - {best_factor})
                else:
                    # 随机选择保留一个因子
                    factors_to_remove.update(correlated_factors)
        
        # 返回保留的因子列表
        remaining_factors = list(all_factors - factors_to_remove)
        return remaining_factors
    
    def select_factors_by_univariate(self, 
                                   factor_data: pd.DataFrame,
                                   target: pd.Series,
                                   k: int = 50,
                                   score_func: str = 'f_regression') -> List[str]:
        """
        使用单变量统计测试选择因子
        
        Args:
            factor_data: 因子数据DataFrame
            target: 目标变量Series
            k: 选择的因子数量
            score_func: 评分函数，'f_regression'或'mutual_info'
            
        Returns:
            选择的因子列表
        """
        # 排除非因子列
        factor_cols = [col for col in factor_data.columns 
                      if col not in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']]
        
        X = factor_data[factor_cols].select_dtypes(include=[np.number])
        y = target
        
        # 对齐数据
        aligned_data = pd.concat([X, y], axis=1).dropna()
        X_aligned = aligned_data.iloc[:, :-1]
        y_aligned = aligned_data.iloc[:, -1]
        
        if len(X_aligned) == 0:
            return []
        
        # 选择评分函数
        if score_func == 'f_regression':
            selector = SelectKBest(score_func=f_regression, k=min(k, X_aligned.shape[1]))
        else:
            selector = SelectKBest(score_func=mutual_info_regression, k=min(k, X_aligned.shape[1]))
        
        # 拟合选择器
        selector.fit(X_aligned, y_aligned)
        
        # 获取选择的因子
        selected_indices = selector.get_support(indices=True)
        selected_factors = [X_aligned.columns[i] for i in selected_indices]
        
        # 保存因子评分
        scores = selector.scores_
        for i, factor in enumerate(X_aligned.columns):
            self.factor_scores[factor] = scores[i] if not np.isnan(scores[i]) else 0
        
        return selected_factors
    
    def select_factors_by_clustering(self, 
                                   factor_data: pd.DataFrame,
                                   n_clusters: int = 10,
                                   selection_method: str = 'ic_best') -> List[str]:
        """
        使用聚类方法选择因子
        
        Args:
            factor_data: 因子数据DataFrame
            n_clusters: 聚类数量
            selection_method: 从每个聚类中选择因子的方法
            
        Returns:
            选择的因子列表
        """
        # 排除非因子列
        factor_cols = [col for col in factor_data.columns 
                      if col not in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']]
        
        X = factor_data[factor_cols].select_dtypes(include=[np.number]).dropna()
        
        if len(X) == 0 or X.shape[1] < n_clusters:
            return list(X.columns)
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(X.T)  # 转置，因为我们要对因子进行聚类
        
        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # 从每个聚类中选择代表性因子
        selected_factors = []
        for cluster_id in range(n_clusters):
            cluster_factors = [factor for i, factor in enumerate(X.columns) 
                             if cluster_labels[i] == cluster_id]
            
            if not cluster_factors:
                continue
            
            if selection_method == 'ic_best' and self.ic_scores:
                # 选择IC最好的因子
                best_factor = None
                best_ic = -1
                for factor in cluster_factors:
                    if factor in self.ic_scores:
                        ic_values = list(self.ic_scores[factor].values())
                        avg_ic = np.mean(np.abs(ic_values))
                        if avg_ic > best_ic:
                            best_ic = avg_ic
                            best_factor = factor
                
                if best_factor:
                    selected_factors.append(best_factor)
                else:
                    selected_factors.append(cluster_factors[0])
            else:
                # 选择第一个因子
                selected_factors.append(cluster_factors[0])
        
        return selected_factors
    
    def apply_pca(self, 
                  factor_data: pd.DataFrame,
                  n_components: Union[int, float] = 0.95,
                  return_components: bool = False) -> Union[pd.DataFrame, Tuple[pd.DataFrame, np.ndarray]]:
        """
        应用主成分分析进行降维
        
        Args:
            factor_data: 因子数据DataFrame
            n_components: 主成分数量或方差解释比例
            return_components: 是否返回主成分载荷
            
        Returns:
            降维后的数据DataFrame，可选返回主成分载荷
        """
        # 排除非因子列
        factor_cols = [col for col in factor_data.columns 
                      if col not in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']]
        
        X = factor_data[factor_cols].select_dtypes(include=[np.number]).dropna()
        
        if len(X) == 0:
            return pd.DataFrame()
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(X)
        
        # 应用PCA
        self.pca_model = PCA(n_components=n_components, random_state=42)
        X_pca = self.pca_model.fit_transform(X_scaled)
        
        # 创建结果DataFrame
        pca_columns = [f'PC{i+1}' for i in range(X_pca.shape[1])]
        result_df = pd.DataFrame(X_pca, index=X.index, columns=pca_columns)
        
        if return_components:
            return result_df, self.pca_model.components_
        else:
            return result_df
    
    def apply_factor_analysis(self, 
                            factor_data: pd.DataFrame,
                            n_factors: int = 10) -> pd.DataFrame:
        """
        应用因子分析进行降维
        
        Args:
            factor_data: 因子数据DataFrame
            n_factors: 因子数量
            
        Returns:
            因子分析结果DataFrame
        """
        # 排除非因子列
        factor_cols = [col for col in factor_data.columns 
                      if col not in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']]
        
        X = factor_data[factor_cols].select_dtypes(include=[np.number]).dropna()
        
        if len(X) == 0:
            return pd.DataFrame()
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(X)
        
        # 应用因子分析
        self.factor_analysis_model = FactorAnalysis(n_components=n_factors, random_state=42)
        X_fa = self.factor_analysis_model.fit_transform(X_scaled)
        
        # 创建结果DataFrame
        fa_columns = [f'Factor{i+1}' for i in range(X_fa.shape[1])]
        result_df = pd.DataFrame(X_fa, index=X.index, columns=fa_columns)
        
        return result_df
    
    def comprehensive_factor_selection(self, 
                                     factor_data: pd.DataFrame,
                                     returns: pd.Series,
                                     max_factors: int = 30,
                                     correlation_threshold: float = 0.8,
                                     ic_weight: float = 0.4,
                                     ir_weight: float = 0.3,
                                     univariate_weight: float = 0.3) -> List[str]:
        """
        综合因子选择方法
        
        Args:
            factor_data: 因子数据DataFrame
            returns: 收益率数据Series
            max_factors: 最大因子数量
            correlation_threshold: 相关性阈值
            ic_weight: IC权重
            ir_weight: IR权重
            univariate_weight: 单变量测试权重
            
        Returns:
            选择的因子列表
        """
        # 1. 计算IC和IR
        ic_scores = self.calculate_ic_scores(factor_data, returns)
        ic_ir_scores = self.calculate_ic_ir_scores(factor_data, returns)
        
        # 2. 单变量选择
        univariate_factors = self.select_factors_by_univariate(
            factor_data, returns.shift(-1), k=max_factors*2
        )
        
        # 3. 计算综合评分
        factor_cols = [col for col in factor_data.columns 
                      if col not in ['date', 'code', 'open', 'high', 'low', 'close', 'volume']]
        
        comprehensive_scores = {}
        for factor in factor_cols:
            score = 0
            
            # IC评分
            if factor in ic_scores:
                ic_values = list(ic_scores[factor].values())
                ic_score = np.mean(np.abs(ic_values))
                score += ic_weight * ic_score
            
            # IR评分
            if factor in ic_ir_scores:
                ir_score = abs(ic_ir_scores[factor]['ir'])
                score += ir_weight * ir_score
            
            # 单变量评分
            if factor in univariate_factors:
                univariate_score = self.factor_scores.get(factor, 0)
                # 标准化评分
                max_univariate = max(self.factor_scores.values()) if self.factor_scores else 1
                normalized_score = univariate_score / (max_univariate + 1e-8)
                score += univariate_weight * normalized_score
            
            comprehensive_scores[factor] = score
        
        # 4. 按评分排序
        sorted_factors = sorted(comprehensive_scores.keys(), 
                              key=lambda x: comprehensive_scores[x], 
                              reverse=True)
        
        # 5. 移除高相关因子
        selected_factors = []
        for factor in sorted_factors:
            if len(selected_factors) >= max_factors:
                break
            
            # 检查与已选因子的相关性
            if self.correlation_matrix is not None:
                is_correlated = False
                for selected_factor in selected_factors:
                    if (factor in self.correlation_matrix.index and 
                        selected_factor in self.correlation_matrix.columns):
                        corr = abs(self.correlation_matrix.loc[factor, selected_factor])
                        if corr > correlation_threshold:
                            is_correlated = True
                            break
                
                if not is_correlated:
                    selected_factors.append(factor)
            else:
                selected_factors.append(factor)
        
        self.selected_factors = selected_factors
        return selected_factors
    
    def get_factor_importance_report(self) -> pd.DataFrame:
        """
        生成因子重要性报告
        
        Returns:
            因子重要性报告DataFrame
        """
        report_data = []
        
        for factor in self.selected_factors:
            factor_info = {'factor_name': factor}
            
            # IC信息
            if factor in self.ic_scores:
                ic_values = list(self.ic_scores[factor].values())
                factor_info['ic_mean'] = np.mean(ic_values)
                factor_info['ic_abs_mean'] = np.mean(np.abs(ic_values))
                factor_info['ic_std'] = np.std(ic_values)
            
            # 单变量评分
            if factor in self.factor_scores:
                factor_info['univariate_score'] = self.factor_scores[factor]
            
            report_data.append(factor_info)
        
        return pd.DataFrame(report_data)


def create_factor_selector() -> FactorSelector:
    """
    创建因子选择器实例
    
    Returns:
        FactorSelector实例
    """
    return FactorSelector()