#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版推荐系统融合策略模块
功能：将机器学习模型预测的上涨概率与原有的多因子线性打分结果结合
融合方式：多种策略包括加权平均、优先过滤、排序微调、动态权重等
输出：统一的JSON格式推荐结果，包含详细的推荐理由和评分细节
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
from dataclasses import dataclass
from enum import Enum

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_predictor import MLPredictor
from scoring_engine import ScoringEngine
from feature_extractor import FeatureExtractor
from data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

class FusionMethod(Enum):
    """融合方法枚举"""
    WEIGHTED_AVERAGE = "weighted_average"  # 加权平均
    FILTER_FIRST = "filter_first"  # 优先过滤
    RANK_ADJUSTMENT = "rank_adjustment"  # 排序微调
    DYNAMIC_WEIGHT = "dynamic_weight"  # 动态权重
    CONSENSUS_BOOST = "consensus_boost"  # 一致性增强

@dataclass
class StockRecommendation:
    """股票推荐结果数据类"""
    rank: int
    stock_code: str
    stock_name: str
    current_price: float
    change_pct: float
    final_score: float
    ml_probability: float
    factor_score: float
    recommendation_reason: str
    confidence_level: str
    risk_level: str
    score_details: Dict
    fusion_method: str
    timestamp: str

class EnhancedFusionStrategy:
    """增强版推荐系统融合策略类"""
    
    def __init__(self, config_path: str = "fusion_config.yaml"):
        """
        初始化增强版融合策略
        
        Args:
            config_path: 融合配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化各个模块
        self.ml_predictor = MLPredictor()
        self.scoring_engine = ScoringEngine()
        self.feature_extractor = FeatureExtractor()
        self.data_fetcher = DataFetcher()
        
        # 融合策略配置
        self.fusion_config = self.config.get('fusion_strategy', {})
        self.method = FusionMethod(self.fusion_config.get('method', 'weighted_average'))
        
        # 权重配置
        self.weights = self.fusion_config.get('weights', {
            'ml_weight': 0.4,
            'factor_weight': 0.6,
            'volume_weight': 0.1,
            'momentum_weight': 0.1
        })
        
        # 阈值配置
        self.thresholds = self.fusion_config.get('thresholds', {
            'ml_threshold': 0.6,
            'factor_threshold': 0.5,
            'confidence_threshold': 0.7,
            'risk_threshold': 0.3
        })
        
        # 输出配置
        self.output_config = self.config.get('output', {})
        self.top_n = self.output_config.get('top_recommendations', 10)
        self.output_dir = self.output_config.get('output_dir', 'results')
        self.include_details = self.output_config.get('include_details', True)
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件{self.config_path}不存在，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'fusion_strategy': {
                'method': 'weighted_average',
                'weights': {
                    'ml_weight': 0.4,
                    'factor_weight': 0.6,
                    'volume_weight': 0.1,
                    'momentum_weight': 0.1
                },
                'thresholds': {
                    'ml_threshold': 0.6,
                    'factor_threshold': 0.5,
                    'confidence_threshold': 0.7,
                    'risk_threshold': 0.3
                }
            },
            'output': {
                'top_recommendations': 10,
                'output_dir': 'results',
                'include_details': True
            }
        }
    
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
                logger.warning("ML模型加载失败，将使用模拟数据")
                return self._generate_mock_ml_predictions(stock_codes)
                
            predictions = self.ml_predictor.predict_today_updown(stock_codes)
            logger.info(f"ML预测完成，获得{len(predictions)}只股票的预测结果")
            return predictions
            
        except Exception as e:
            logger.error(f"获取ML预测失败: {e}，使用模拟数据")
            return self._generate_mock_ml_predictions(stock_codes)
    
    def _generate_mock_ml_predictions(self, stock_codes: List[str]) -> Dict[str, float]:
        """生成模拟ML预测数据（用于演示）"""
        if stock_codes is None:
            stock_codes = self._get_default_stock_universe()
        
        np.random.seed(42)  # 确保结果可重现
        predictions = {}
        for code in stock_codes:
            # 生成0.3到0.8之间的随机概率
            prob = np.random.uniform(0.3, 0.8)
            predictions[code] = prob
        
        return predictions
    
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
            
            # 如果特征提取失败，使用模拟数据
            if not all_features:
                logger.warning("特征提取失败，使用模拟数据")
                return self._generate_mock_factor_scores(stock_codes)
            
            # 进行因子打分
            scored_stocks = self.scoring_engine.score_stocks(all_features)
            logger.info(f"因子打分完成，获得{len(scored_stocks)}只股票的打分结果")
            return scored_stocks
            
        except Exception as e:
            logger.error(f"获取因子打分失败: {e}，使用模拟数据")
            return self._generate_mock_factor_scores(stock_codes)
    
    def _generate_mock_factor_scores(self, stock_codes: List[str]) -> List[Dict]:
        """生成模拟因子打分数据（用于演示）"""
        stock_names = {
            '000001': '平安银行', '000002': '万科A', '000858': '五粮液',
            '000876': '新希望', '002415': '海康威视', '600000': '浦发银行',
            '600036': '招商银行', '600519': '贵州茅台', '600887': '伊利股份',
            '601318': '中国平安'
        }
        
        np.random.seed(42)
        factor_scores = []
        
        for code in stock_codes:
            score = {
                'stock_code': code,
                'stock_name': stock_names.get(code, f'股票{code}'),
                'current_price': np.random.uniform(10, 200),
                'change_pct': np.random.uniform(-5, 5),
                'total_score': np.random.uniform(-1, 2),
                'recommendation_reason': '技术指标良好，资金流入积极',
                'score_details': {
                    'momentum_score': np.random.uniform(-0.5, 1),
                    'volume_score': np.random.uniform(-0.5, 1),
                    'technical_score': np.random.uniform(-0.5, 1),
                    'sentiment_score': np.random.uniform(-0.5, 1)
                }
            }
            factor_scores.append(score)
        
        return factor_scores
    
    def _get_default_stock_universe(self) -> List[str]:
        """获取默认股票池"""
        return [
            '000001', '000002', '000858', '000876', '002415',
            '600000', '600036', '600519', '600887', '601318'
        ]
    
    def calculate_confidence_level(self, ml_prob: float, factor_score: float) -> str:
        """
        计算置信度等级
        
        Args:
            ml_prob: ML预测概率
            factor_score: 因子得分
            
        Returns:
            置信度等级: 'high', 'medium', 'low'
        """
        # ML概率和因子得分的一致性
        ml_signal = 1 if ml_prob > 0.5 else -1
        factor_signal = 1 if factor_score > 0 else -1
        
        # 信号强度
        ml_strength = abs(ml_prob - 0.5) * 2  # 0-1
        factor_strength = min(abs(factor_score), 2) / 2  # 0-1
        
        # 一致性加权
        if ml_signal == factor_signal:
            confidence = (ml_strength + factor_strength) / 2
        else:
            confidence = abs(ml_strength - factor_strength) / 2
        
        if confidence >= self.thresholds['confidence_threshold']:
            return 'high'
        elif confidence >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def calculate_risk_level(self, ml_prob: float, factor_score: float, volatility: float = None) -> str:
        """
        计算风险等级
        
        Args:
            ml_prob: ML预测概率
            factor_score: 因子得分
            volatility: 波动率（可选）
            
        Returns:
            风险等级: 'low', 'medium', 'high'
        """
        # 基于预测不确定性计算风险
        ml_uncertainty = 1 - abs(ml_prob - 0.5) * 2
        factor_uncertainty = 1 - min(abs(factor_score), 2) / 2
        
        risk_score = (ml_uncertainty + factor_uncertainty) / 2
        
        # 如果有波动率信息，加入考虑
        if volatility is not None:
            risk_score = (risk_score + min(volatility, 1)) / 2
        
        if risk_score <= self.thresholds['risk_threshold']:
            return 'low'
        elif risk_score <= 0.6:
            return 'medium'
        else:
            return 'high'
    
    def weighted_average_fusion(self, 
                              ml_predictions: Dict[str, float], 
                              factor_scores: List[Dict]) -> List[StockRecommendation]:
        """
        加权平均融合策略
        
        Args:
            ml_predictions: ML预测结果
            factor_scores: 因子打分结果
            
        Returns:
            融合后的推荐结果
        """
        logger.info("执行加权平均融合策略...")
        
        factor_dict = {stock['stock_code']: stock for stock in factor_scores}
        fused_results = []
        
        for stock_code, ml_prob in ml_predictions.items():
            if stock_code not in factor_dict:
                continue
                
            factor_stock = factor_dict[stock_code]
            factor_score = factor_stock['total_score']
            
            # 标准化分数
            normalized_ml_prob = max(0, min(1, ml_prob))
            normalized_factor_score = max(0, min(1, (factor_score + 2) / 4))
            
            # 加权平均计算最终得分
            final_score = (
                self.weights['ml_weight'] * normalized_ml_prob + 
                self.weights['factor_weight'] * normalized_factor_score
            )
            
            # 计算置信度和风险等级
            confidence = self.calculate_confidence_level(ml_prob, factor_score)
            risk = self.calculate_risk_level(ml_prob, factor_score)
            
            # 生成推荐理由
            ml_reason = f"ML预测上涨概率{ml_prob:.1%}"
            factor_reason = factor_stock.get('recommendation_reason', '因子表现良好')
            fusion_reason = f"{ml_reason}；{factor_reason}；置信度{confidence}，风险{risk}"
            
            recommendation = StockRecommendation(
                rank=0,  # 稍后排序时设置
                stock_code=stock_code,
                stock_name=factor_stock.get('stock_name', ''),
                current_price=factor_stock.get('current_price', 0),
                change_pct=factor_stock.get('change_pct', 0),
                final_score=final_score,
                ml_probability=ml_prob,
                factor_score=factor_score,
                recommendation_reason=fusion_reason,
                confidence_level=confidence,
                risk_level=risk,
                score_details={
                    'normalized_ml_prob': normalized_ml_prob,
                    'normalized_factor_score': normalized_factor_score,
                    'ml_weight': self.weights['ml_weight'],
                    'factor_weight': self.weights['factor_weight'],
                    **factor_stock.get('score_details', {})
                },
                fusion_method='weighted_average',
                timestamp=datetime.now().isoformat()
            )
            
            fused_results.append(recommendation)
        
        # 按最终得分排序并设置排名
        fused_results.sort(key=lambda x: x.final_score, reverse=True)
        for i, result in enumerate(fused_results):
            result.rank = i + 1
        
        return fused_results
    
    def filter_first_fusion(self, 
                           ml_predictions: Dict[str, float], 
                           factor_scores: List[Dict]) -> List[StockRecommendation]:
        """
        优先过滤融合策略：先用ML模型过滤，再用因子模型排序
        """
        logger.info("执行优先过滤融合策略...")
        
        factor_dict = {stock['stock_code']: stock for stock in factor_scores}
        
        # 第一步：ML模型过滤
        ml_filtered = {code: prob for code, prob in ml_predictions.items() 
                      if prob >= self.thresholds['ml_threshold']}
        
        logger.info(f"ML过滤后剩余{len(ml_filtered)}只股票")
        
        fused_results = []
        
        for stock_code, ml_prob in ml_filtered.items():
            if stock_code not in factor_dict:
                continue
                
            factor_stock = factor_dict[stock_code]
            factor_score = factor_stock['total_score']
            
            # 进一步过滤：因子得分也要达到阈值
            if factor_score < self.thresholds['factor_threshold']:
                continue
            
            # 最终得分主要基于因子得分，ML概率作为加分项
            final_score = factor_score + (ml_prob - 0.5) * 0.5
            
            confidence = self.calculate_confidence_level(ml_prob, factor_score)
            risk = self.calculate_risk_level(ml_prob, factor_score)
            
            fusion_reason = (
                f"ML预测概率{ml_prob:.1%}(>{self.thresholds['ml_threshold']:.1%})；"
                f"{factor_stock.get('recommendation_reason', '因子表现良好')}；"
                f"置信度{confidence}，风险{risk}"
            )
            
            recommendation = StockRecommendation(
                rank=0,
                stock_code=stock_code,
                stock_name=factor_stock.get('stock_name', ''),
                current_price=factor_stock.get('current_price', 0),
                change_pct=factor_stock.get('change_pct', 0),
                final_score=final_score,
                ml_probability=ml_prob,
                factor_score=factor_score,
                recommendation_reason=fusion_reason,
                confidence_level=confidence,
                risk_level=risk,
                score_details={
                    'ml_threshold': self.thresholds['ml_threshold'],
                    'factor_threshold': self.thresholds['factor_threshold'],
                    **factor_stock.get('score_details', {})
                },
                fusion_method='filter_first',
                timestamp=datetime.now().isoformat()
            )
            
            fused_results.append(recommendation)
        
        # 按最终得分排序并设置排名
        fused_results.sort(key=lambda x: x.final_score, reverse=True)
        for i, result in enumerate(fused_results):
            result.rank = i + 1
        
        return fused_results
    
    def consensus_boost_fusion(self, 
                             ml_predictions: Dict[str, float], 
                             factor_scores: List[Dict]) -> List[StockRecommendation]:
        """
        一致性增强融合策略：当ML和因子模型预测一致时给予额外加分
        """
        logger.info("执行一致性增强融合策略...")
        
        factor_dict = {stock['stock_code']: stock for stock in factor_scores}
        fused_results = []
        
        for stock_code, ml_prob in ml_predictions.items():
            if stock_code not in factor_dict:
                continue
                
            factor_stock = factor_dict[stock_code]
            factor_score = factor_stock['total_score']
            
            # 基础加权平均
            normalized_ml_prob = max(0, min(1, ml_prob))
            normalized_factor_score = max(0, min(1, (factor_score + 2) / 4))
            
            base_score = (
                self.weights['ml_weight'] * normalized_ml_prob + 
                self.weights['factor_weight'] * normalized_factor_score
            )
            
            # 一致性加分
            ml_signal = 1 if ml_prob > 0.5 else -1
            factor_signal = 1 if factor_score > 0 else -1
            
            consensus_bonus = 0
            if ml_signal == factor_signal:
                # 信号一致，根据强度给予加分
                ml_strength = abs(ml_prob - 0.5) * 2
                factor_strength = min(abs(factor_score), 2) / 2
                consensus_bonus = (ml_strength + factor_strength) / 2 * 0.2  # 最多20%加分
            
            final_score = base_score + consensus_bonus
            
            confidence = self.calculate_confidence_level(ml_prob, factor_score)
            risk = self.calculate_risk_level(ml_prob, factor_score)
            
            consensus_desc = "高度一致" if consensus_bonus > 0.1 else "一致" if consensus_bonus > 0 else "分歧"
            fusion_reason = (
                f"ML预测{ml_prob:.1%}，因子得分{factor_score:.2f}，"
                f"预测{consensus_desc}(+{consensus_bonus:.1%})；"
                f"置信度{confidence}，风险{risk}"
            )
            
            recommendation = StockRecommendation(
                rank=0,
                stock_code=stock_code,
                stock_name=factor_stock.get('stock_name', ''),
                current_price=factor_stock.get('current_price', 0),
                change_pct=factor_stock.get('change_pct', 0),
                final_score=final_score,
                ml_probability=ml_prob,
                factor_score=factor_score,
                recommendation_reason=fusion_reason,
                confidence_level=confidence,
                risk_level=risk,
                score_details={
                    'base_score': base_score,
                    'consensus_bonus': consensus_bonus,
                    'consensus_desc': consensus_desc,
                    **factor_stock.get('score_details', {})
                },
                fusion_method='consensus_boost',
                timestamp=datetime.now().isoformat()
            )
            
            fused_results.append(recommendation)
        
        # 按最终得分排序并设置排名
        fused_results.sort(key=lambda x: x.final_score, reverse=True)
        for i, result in enumerate(fused_results):
            result.rank = i + 1
        
        return fused_results
    
    def run_fusion(self, stock_codes: List[str] = None) -> List[StockRecommendation]:
        """
        运行融合推荐
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            融合推荐结果
        """
        logger.info(f"开始运行融合推荐，方法: {self.method.value}")
        
        # 获取ML预测和因子打分
        ml_predictions = self.get_ml_predictions(stock_codes)
        factor_scores = self.get_factor_scores(stock_codes)
        
        if not ml_predictions or not factor_scores:
            logger.error("无法获取ML预测或因子打分结果")
            return []
        
        # 根据选择的方法进行融合
        if self.method == FusionMethod.WEIGHTED_AVERAGE:
            results = self.weighted_average_fusion(ml_predictions, factor_scores)
        elif self.method == FusionMethod.FILTER_FIRST:
            results = self.filter_first_fusion(ml_predictions, factor_scores)
        elif self.method == FusionMethod.CONSENSUS_BOOST:
            results = self.consensus_boost_fusion(ml_predictions, factor_scores)
        else:
            logger.warning(f"未知的融合方法: {self.method.value}，使用加权平均")
            results = self.weighted_average_fusion(ml_predictions, factor_scores)
        
        # 返回Top N结果
        return results[:self.top_n]
    
    def save_results_to_json(self, results: List[StockRecommendation], filename: str = None) -> str:
        """
        保存结果到JSON文件
        
        Args:
            results: 推荐结果列表
            filename: 文件名（可选）
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fusion_recommendations_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 转换为字典格式
        output_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'fusion_method': self.method.value,
                'total_recommendations': len(results),
                'top_n': self.top_n,
                'config': {
                    'weights': self.weights,
                    'thresholds': self.thresholds
                }
            },
            'recommendations': []
        }
        
        for result in results:
            rec_dict = {
                'rank': result.rank,
                'stock_code': result.stock_code,
                'stock_name': result.stock_name,
                'current_price': round(result.current_price, 2),
                'change_pct': round(result.change_pct, 2),
                'final_score': round(result.final_score, 4),
                'ml_probability': round(result.ml_probability, 4),
                'factor_score': round(result.factor_score, 4),
                'recommendation_reason': result.recommendation_reason,
                'confidence_level': result.confidence_level,
                'risk_level': result.risk_level,
                'fusion_method': result.fusion_method,
                'timestamp': result.timestamp
            }
            
            # 如果需要包含详细信息
            if self.include_details:
                rec_dict['score_details'] = result.score_details
            
            output_data['recommendations'].append(rec_dict)
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"推荐结果已保存到: {filepath}")
        return filepath
    
    def print_results_summary(self, results: List[StockRecommendation]):
        """
        打印结果摘要
        
        Args:
            results: 推荐结果列表
        """
        if not results:
            print("没有推荐结果")
            return
        
        print(f"\n=== 融合推荐结果摘要 (方法: {self.method.value}) ===")
        print(f"{'排名':<4} {'股票代码':<8} {'股票名称':<12} {'最终得分':<8} {'ML概率':<8} {'因子得分':<8} {'置信度':<6} {'风险':<6}")
        print("-" * 80)
        
        for result in results:
            print(f"{result.rank:<4} {result.stock_code:<8} {result.stock_name:<12} "
                  f"{result.final_score:<8.3f} {result.ml_probability:<8.3f} "
                  f"{result.factor_score:<8.3f} {result.confidence_level:<6} {result.risk_level:<6}")
        
        # 统计信息
        high_confidence = sum(1 for r in results if r.confidence_level == 'high')
        low_risk = sum(1 for r in results if r.risk_level == 'low')
        avg_ml_prob = np.mean([r.ml_probability for r in results])
        avg_factor_score = np.mean([r.factor_score for r in results])
        
        print(f"\n=== 统计信息 ===")
        print(f"高置信度推荐: {high_confidence}/{len(results)}")
        print(f"低风险推荐: {low_risk}/{len(results)}")
        print(f"平均ML概率: {avg_ml_prob:.3f}")
        print(f"平均因子得分: {avg_factor_score:.3f}")

def main():
    """主函数 - 演示融合策略"""
    print("增强版推荐系统融合策略演示")
    print("=" * 50)
    
    # 创建融合策略实例
    fusion = EnhancedFusionStrategy()
    
    # 测试不同的融合方法
    methods = [FusionMethod.WEIGHTED_AVERAGE, FusionMethod.FILTER_FIRST, FusionMethod.CONSENSUS_BOOST]
    
    for method in methods:
        print(f"\n测试融合方法: {method.value}")
        fusion.method = method
        
        # 运行融合推荐
        results = fusion.run_fusion()
        
        if results:
            # 打印结果摘要
            fusion.print_results_summary(results)
            
            # 保存结果
            filename = f"demo_{method.value}_results.json"
            filepath = fusion.save_results_to_json(results, filename)
            print(f"结果已保存到: {filepath}")
        else:
            print("没有生成推荐结果")
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()