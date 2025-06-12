#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐系统融合策略模块
功能：将机器学习模型预测的上涨概率与原有的多因子线性打分结果结合
融合方式：加权平均、优先过滤、排序微调等多种策略
输出：统一的JSON格式推荐结果
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import logging
import yaml

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_predictor import MLPredictor
from scoring_engine import ScoringEngine
from feature_extractor import FeatureExtractor
from data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

class RecommendationFusion:
    """推荐系统融合策略类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化融合策略
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化各个模块
        self.ml_predictor = MLPredictor(config_path)
        self.scoring_engine = ScoringEngine(config_path)
        self.feature_extractor = FeatureExtractor(config_path)
        self.data_fetcher = DataFetcher(config_path)
        
        # 融合策略配置
        self.fusion_config = self.config.get('fusion_strategy', {})
        self.fusion_method = self.fusion_config.get('method', 'weighted_average')  # weighted_average, filter_first, rank_adjustment
        self.ml_weight = self.fusion_config.get('ml_weight', 0.4)  # ML模型权重
        self.factor_weight = self.fusion_config.get('factor_weight', 0.6)  # 因子模型权重
        self.ml_threshold = self.fusion_config.get('ml_threshold', 0.6)  # ML概率阈值
        self.factor_threshold = self.fusion_config.get('factor_threshold', 0.5)  # 因子得分阈值
        
        # 输出配置
        self.output_config = self.config.get('output', {})
        self.top_n = self.output_config.get('top_recommendations', 10)
        self.output_dir = self.output_config.get('output_dir', 'results')
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def get_ml_predictions(self, stock_codes: List[str] = None) -> Dict[str, float]:
        """
        获取机器学习模型预测结果
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            股票代码到上涨概率的字典
        """
        logger.info("获取机器学习预测结果...")
        
        try:
            # 确保模型已加载
            if not self.ml_predictor.load_model():
                logger.warning("ML模型加载失败，将使用默认概率")
                return {}
                
            predictions = self.ml_predictor.predict_today_updown(stock_codes)
            logger.info(f"ML预测完成，获得{len(predictions)}只股票的预测结果")
            return predictions
            
        except Exception as e:
            logger.error(f"获取ML预测失败: {e}")
            return {}
    
    def get_factor_scores(self, stock_codes: List[str] = None) -> List[Dict]:
        """
        获取多因子打分结果
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            因子打分结果列表
        """
        logger.info("获取多因子打分结果...")
        
        try:
            # 获取股票特征
            if stock_codes is None:
                stock_codes = self._get_default_stock_universe()
                
            all_features = {}
            for stock_code in stock_codes:
                try:
                    features = self.feature_extractor.extract_all_features(stock_code)
                    if features:
                        all_features[stock_code] = features
                except Exception as e:
                    logger.warning(f"提取股票{stock_code}特征失败: {e}")
                    continue
            
            # 进行因子打分
            scored_stocks = self.scoring_engine.score_stocks(all_features)
            logger.info(f"因子打分完成，获得{len(scored_stocks)}只股票的打分结果")
            return scored_stocks
            
        except Exception as e:
            logger.error(f"获取因子打分失败: {e}")
            return []
    
    def _get_default_stock_universe(self) -> List[str]:
        """获取默认股票池"""
        # 这里可以根据配置或者从数据源获取股票列表
        # 暂时返回一些示例股票代码
        return [
            '000001', '000002', '000858', '000876', '002415',
            '600000', '600036', '600519', '600887', '601318'
        ]
    
    def weighted_average_fusion(self, 
                              ml_predictions: Dict[str, float], 
                              factor_scores: List[Dict]) -> List[Dict]:
        """
        加权平均融合策略
        
        Args:
            ml_predictions: ML预测结果
            factor_scores: 因子打分结果
            
        Returns:
            融合后的推荐结果
        """
        logger.info("执行加权平均融合策略...")
        
        # 创建因子得分字典
        factor_dict = {stock['stock_code']: stock for stock in factor_scores}
        
        fused_results = []
        
        for stock_code, ml_prob in ml_predictions.items():
            if stock_code not in factor_dict:
                continue
                
            factor_stock = factor_dict[stock_code]
            factor_score = factor_stock['total_score']
            
            # 标准化ML概率到0-1范围（如果需要）
            normalized_ml_prob = max(0, min(1, ml_prob))
            
            # 标准化因子得分到0-1范围
            # 假设因子得分范围在-2到2之间
            normalized_factor_score = max(0, min(1, (factor_score + 2) / 4))
            
            # 加权平均计算最终得分
            final_score = (self.ml_weight * normalized_ml_prob + 
                          self.factor_weight * normalized_factor_score)
            
            # 生成融合推荐理由
            ml_reason = f"ML预测上涨概率{ml_prob:.1%}"
            factor_reason = factor_stock.get('recommendation_reason', '因子表现良好')
            fusion_reason = f"{ml_reason}; {factor_reason}"
            
            fused_result = {
                'stock_code': stock_code,
                'stock_name': factor_stock.get('stock_name', ''),
                'current_price': factor_stock.get('current_price', 0),
                'change_pct': factor_stock.get('change_pct', 0),
                'final_score': final_score,
                'ml_probability': ml_prob,
                'factor_score': factor_score,
                'normalized_ml_prob': normalized_ml_prob,
                'normalized_factor_score': normalized_factor_score,
                'recommendation_reason': fusion_reason,
                'score_details': factor_stock.get('score_details', {}),
                'fusion_method': 'weighted_average',
                'ml_weight': self.ml_weight,
                'factor_weight': self.factor_weight
            }
            
            fused_results.append(fused_result)
        
        # 按最终得分排序
        fused_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return fused_results
    
    def filter_first_fusion(self, 
                           ml_predictions: Dict[str, float], 
                           factor_scores: List[Dict]) -> List[Dict]:
        """
        优先过滤融合策略：先用ML模型过滤，再用因子模型排序
        
        Args:
            ml_predictions: ML预测结果
            factor_scores: 因子打分结果
            
        Returns:
            融合后的推荐结果
        """
        logger.info("执行优先过滤融合策略...")
        
        # 创建因子得分字典
        factor_dict = {stock['stock_code']: stock for stock in factor_scores}
        
        # 第一步：ML模型过滤
        ml_filtered = {code: prob for code, prob in ml_predictions.items() 
                      if prob >= self.ml_threshold}
        
        logger.info(f"ML过滤后剩余{len(ml_filtered)}只股票")
        
        # 第二步：在过滤后的股票中按因子得分排序
        fused_results = []
        
        for stock_code, ml_prob in ml_filtered.items():
            if stock_code not in factor_dict:
                continue
                
            factor_stock = factor_dict[stock_code]
            factor_score = factor_stock['total_score']
            
            # 进一步过滤：因子得分也要达到阈值
            if factor_score < self.factor_threshold:
                continue
            
            # 最终得分主要基于因子得分，ML概率作为加分项
            final_score = factor_score + (ml_prob - 0.5) * 0.5  # ML概率的贡献较小
            
            fusion_reason = f"ML预测概率{ml_prob:.1%}(>{self.ml_threshold:.1%}); {factor_stock.get('recommendation_reason', '因子表现良好')}"
            
            fused_result = {
                'stock_code': stock_code,
                'stock_name': factor_stock.get('stock_name', ''),
                'current_price': factor_stock.get('current_price', 0),
                'change_pct': factor_stock.get('change_pct', 0),
                'final_score': final_score,
                'ml_probability': ml_prob,
                'factor_score': factor_score,
                'recommendation_reason': fusion_reason,
                'score_details': factor_stock.get('score_details', {}),
                'fusion_method': 'filter_first',
                'ml_threshold': self.ml_threshold,
                'factor_threshold': self.factor_threshold
            }
            
            fused_results.append(fused_result)
        
        # 按最终得分排序
        fused_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return fused_results
    
    def rank_adjustment_fusion(self, 
                             ml_predictions: Dict[str, float], 
                             factor_scores: List[Dict]) -> List[Dict]:
        """
        排序微调融合策略：基于因子排序，用ML预测进行微调
        
        Args:
            ml_predictions: ML预测结果
            factor_scores: 因子打分结果
            
        Returns:
            融合后的推荐结果
        """
        logger.info("执行排序微调融合策略...")
        
        # 先按因子得分排序
        factor_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        fused_results = []
        
        for factor_stock in factor_scores:
            stock_code = factor_stock['stock_code']
            
            if stock_code not in ml_predictions:
                continue
                
            ml_prob = ml_predictions[stock_code]
            factor_score = factor_stock['total_score']
            
            # 排序微调：ML概率高的股票得到排序提升
            rank_adjustment = (ml_prob - 0.5) * 2  # 调整范围 -1 到 1
            final_score = factor_score + rank_adjustment
            
            fusion_reason = f"因子得分{factor_score:.2f}, ML预测{ml_prob:.1%}调整; {factor_stock.get('recommendation_reason', '')}"
            
            fused_result = {
                'stock_code': stock_code,
                'stock_name': factor_stock.get('stock_name', ''),
                'current_price': factor_stock.get('current_price', 0),
                'change_pct': factor_stock.get('change_pct', 0),
                'final_score': final_score,
                'ml_probability': ml_prob,
                'factor_score': factor_score,
                'rank_adjustment': rank_adjustment,
                'recommendation_reason': fusion_reason,
                'score_details': factor_stock.get('score_details', {}),
                'fusion_method': 'rank_adjustment'
            }
            
            fused_results.append(fused_result)
        
        # 按调整后的得分重新排序
        fused_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return fused_results
    
    def execute_fusion(self, stock_codes: List[str] = None) -> List[Dict]:
        """
        执行融合策略
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            融合后的推荐结果
        """
        logger.info(f"开始执行融合策略: {self.fusion_method}")
        
        # 获取ML预测和因子打分
        ml_predictions = self.get_ml_predictions(stock_codes)
        factor_scores = self.get_factor_scores(stock_codes)
        
        if not ml_predictions and not factor_scores:
            logger.error("无法获取ML预测和因子打分结果")
            return []
        
        # 如果只有一种结果，使用单一策略
        if not ml_predictions:
            logger.warning("ML预测结果为空，仅使用因子打分")
            return factor_scores[:self.top_n]
        
        if not factor_scores:
            logger.warning("因子打分结果为空，仅使用ML预测")
            ml_only_results = []
            for stock_code, prob in list(ml_predictions.items())[:self.top_n]:
                ml_only_results.append({
                    'stock_code': stock_code,
                    'final_score': prob,
                    'ml_probability': prob,
                    'factor_score': 0,
                    'recommendation_reason': f"ML预测上涨概率{prob:.1%}",
                    'fusion_method': 'ml_only'
                })
            return ml_only_results
        
        # 根据配置选择融合方法
        if self.fusion_method == 'weighted_average':
            fused_results = self.weighted_average_fusion(ml_predictions, factor_scores)
        elif self.fusion_method == 'filter_first':
            fused_results = self.filter_first_fusion(ml_predictions, factor_scores)
        elif self.fusion_method == 'rank_adjustment':
            fused_results = self.rank_adjustment_fusion(ml_predictions, factor_scores)
        else:
            logger.warning(f"未知的融合方法: {self.fusion_method}，使用默认加权平均")
            fused_results = self.weighted_average_fusion(ml_predictions, factor_scores)
        
        return fused_results[:self.top_n]
    
    def format_final_results(self, fused_results: List[Dict]) -> Dict:
        """
        格式化最终推荐结果
        
        Args:
            fused_results: 融合后的结果
            
        Returns:
            格式化的JSON结果
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        formatted_results = []
        
        for i, result in enumerate(fused_results, 1):
            formatted_result = {
                'rank': i,
                'stock_code': result['stock_code'],
                'stock_name': result.get('stock_name', ''),
                'current_price': round(result.get('current_price', 0), 2),
                'change_pct': round(result.get('change_pct', 0), 2),
                'final_score': round(result['final_score'], 4),
                'ml_probability': round(result.get('ml_probability', 0), 4),
                'factor_score': round(result.get('factor_score', 0), 4),
                'recommendation_reason': result.get('recommendation_reason', ''),
                'fusion_details': {
                    'method': result.get('fusion_method', self.fusion_method),
                    'ml_weight': result.get('ml_weight', self.ml_weight),
                    'factor_weight': result.get('factor_weight', self.factor_weight),
                    'ml_threshold': result.get('ml_threshold', self.ml_threshold),
                    'factor_threshold': result.get('factor_threshold', self.factor_threshold)
                },
                'score_breakdown': result.get('score_details', {})
            }
            
            formatted_results.append(formatted_result)
        
        final_output = {
            'metadata': {
                'timestamp': timestamp,
                'fusion_method': self.fusion_method,
                'total_recommendations': len(formatted_results),
                'top_n': self.top_n,
                'ml_weight': self.ml_weight,
                'factor_weight': self.factor_weight,
                'version': '1.0.0'
            },
            'recommendations': formatted_results,
            'summary': {
                'avg_final_score': round(np.mean([r['final_score'] for r in formatted_results]), 4) if formatted_results else 0,
                'avg_ml_probability': round(np.mean([r['ml_probability'] for r in formatted_results]), 4) if formatted_results else 0,
                'avg_factor_score': round(np.mean([r['factor_score'] for r in formatted_results]), 4) if formatted_results else 0,
                'score_range': {
                    'min': round(min([r['final_score'] for r in formatted_results]), 4) if formatted_results else 0,
                    'max': round(max([r['final_score'] for r in formatted_results]), 4) if formatted_results else 0
                }
            }
        }
        
        return final_output
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """
        保存结果到JSON文件
        
        Args:
            results: 推荐结果
            filename: 文件名，如果为None则自动生成
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fusion_recommendations_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"推荐结果已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return ""
    
    def run_fusion_recommendation(self, 
                                stock_codes: List[str] = None, 
                                save_to_file: bool = True) -> Dict:
        """
        运行完整的融合推荐流程
        
        Args:
            stock_codes: 股票代码列表
            save_to_file: 是否保存到文件
            
        Returns:
            最终推荐结果
        """
        logger.info("开始运行融合推荐系统...")
        
        try:
            # 执行融合策略
            fused_results = self.execute_fusion(stock_codes)
            
            if not fused_results:
                logger.warning("未获得任何推荐结果")
                return {'metadata': {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, 
                       'recommendations': [], 'summary': {}}
            
            # 格式化结果
            final_results = self.format_final_results(fused_results)
            
            # 保存到文件
            if save_to_file:
                self.save_results(final_results)
            
            logger.info(f"融合推荐完成，共推荐{len(final_results['recommendations'])}只股票")
            
            return final_results
            
        except Exception as e:
            logger.error(f"融合推荐过程出错: {e}")
            return {'error': str(e), 'metadata': {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}


if __name__ == "__main__":
    # 示例用法
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建融合推荐系统
    fusion_system = RecommendationFusion()
    
    # 运行推荐
    results = fusion_system.run_fusion_recommendation()
    
    # 打印结果摘要
    if 'recommendations' in results:
        print(f"\n=== 融合推荐结果 ===")
        print(f"推荐时间: {results['metadata']['timestamp']}")
        print(f"融合方法: {results['metadata']['fusion_method']}")
        print(f"推荐数量: {results['metadata']['total_recommendations']}")
        print(f"\nTop 5 推荐:")
        
        for i, rec in enumerate(results['recommendations'][:5], 1):
            print(f"{i}. {rec['stock_code']} {rec['stock_name']}")
            print(f"   最终得分: {rec['final_score']:.4f}")
            print(f"   ML概率: {rec['ml_probability']:.1%}")
            print(f"   因子得分: {rec['factor_score']:.2f}")
            print(f"   推荐理由: {rec['recommendation_reason']}")
            print()
    else:
        print("推荐失败:", results.get('error', '未知错误'))