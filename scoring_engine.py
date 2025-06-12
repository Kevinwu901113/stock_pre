#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打分引擎模块
功能：多因子加权打分并排序，返回Top推荐股票
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
import yaml
import os

logger = logging.getLogger(__name__)

class ScoringEngine:
    """打分引擎类"""
    
    def __init__(self, config_path: str = "config.yaml", factor_strategy: str = 'default', stock_universe: str = 'default'):
        """初始化打分引擎
        
        Args:
            config_path: 配置文件路径
            factor_strategy: 因子策略名称
            stock_universe: 股票池名称
        """
        self.config = self._load_config(config_path)
        self.factor_strategy = factor_strategy
        self.stock_universe = stock_universe
        
        # 根据策略选择因子权重
        factor_weights_config = self.config.get('factor_weights', {})
        self.factor_weights = factor_weights_config.get(factor_strategy, factor_weights_config.get('default', {}))
        
        # 根据股票池选择推荐配置
        recommendation_config = self.config.get('recommendation', {})
        stock_pools = self.config.get('stock_pools', {})
        pool_config = stock_pools.get(stock_universe, stock_pools.get('default', {}))
        
        # 合并推荐配置和股票池配置
        self.recommendation_config = {**recommendation_config, **pool_config.get('recommendation', {})}
        self.risk_control_config = self.config.get('risk_control', {})
        
        # 推荐配置
        self.top_recommendations = self.recommendation_config.get('top_recommendations', 20)
        self.min_score_threshold = self.recommendation_config.get('min_score_threshold', 0.6)
        self.sector_diversification = self.recommendation_config.get('sector_diversification', True)
        
        # 风险控制配置
        self.max_daily_recommendations = self.risk_control_config.get('max_daily_recommendations', 20)
        self.min_liquidity_threshold = self.risk_control_config.get('min_liquidity_threshold', 1000000)
        self.volatility_limit = self.risk_control_config.get('volatility_limit', 0.1)
        
        # 如果没有配置因子权重，使用默认权重
        if not self.factor_weights:
            self.factor_weights = self._get_default_factor_weights()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return {}
        
    def _get_default_factor_weights(self) -> Dict[str, float]:
        """加载因子配置"""
        default_weights = {
            # 动量因子权重
            'momentum_5d': 0.10,
            'momentum_10d': 0.10,
            'momentum_20d': 0.10,
            'rsi': 0.05,
            
            # 成交量因子权重
            'volume_ratio': 0.08,
            'volume_spike': 0.07,
            'turnover_rate': 0.05,
            
            # 资金流向因子权重
            'main_inflow_score': 0.10,
            'large_inflow_score': 0.05,
            'capital_strength': 0.05,
            
            # 技术指标权重
            'macd': 0.05,
            'bollinger_position': 0.03,
            
            # 情绪因子权重
            'news_sentiment_score': 0.08,
            'market_sentiment_score': 0.04,
            'overall_sentiment': 0.05,
            
            # 风险因子权重（负权重）
            'volatility_20d': -0.05,
            'price_stability': 0.03,
            
            # 其他因子
            'change_pct': 0.02
        }
        
        logger.info("使用默认因子权重")
        return default_weights
    
    def _is_valid_number(self, value) -> bool:
        """检查值是否为有效数字"""
        try:
            if value is None:
                return False
            if isinstance(value, str):
                if value.strip() == '' or value.lower() in ['nan', 'none', 'null']:
                    return False
                float(value)  # 尝试转换
                return True
            if isinstance(value, (int, float)):
                return not (np.isnan(value) or np.isinf(value))
            return False
        except (ValueError, TypeError):
            return False
    
    def normalize_features(self, features_dict: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """标准化特征 - 支持动态因子名称"""
        if not features_dict:
            return {}
        
        # 收集所有特征值
        all_features = {}
        for stock_code, features in features_dict.items():
            for feature_name, value in features.items():
                if feature_name not in all_features:
                    all_features[feature_name] = []
                all_features[feature_name].append(value)
        
        # 计算每个特征的均值和标准差
        feature_stats = {}
        for feature_name, values in all_features.items():
            values = np.array(values)
            feature_stats[feature_name] = {
                'mean': np.mean(values),
                'std': np.std(values) if np.std(values) > 0 else 1
            }
        
        # 标准化
        normalized_features = {}
        for stock_code, features in features_dict.items():
            normalized_features[stock_code] = {}
            for feature_name, value in features.items():
                stats = feature_stats[feature_name]
                normalized_value = (value - stats['mean']) / stats['std']
                normalized_features[stock_code][feature_name] = normalized_value
        
        return normalized_features
    
    def calculate_momentum_score(self, features: Dict[str, float]) -> Tuple[float, str]:
        """计算动量得分"""
        momentum_factors = ['momentum_5d', 'momentum_10d', 'momentum_20d', 'rsi']
        
        score = 0
        reasons = []
        
        for factor in momentum_factors:
            if factor in features and factor in self.factor_weights:
                factor_score = features[factor] * self.factor_weights[factor]
                score += factor_score
                
                if factor == 'rsi':
                    if features[factor] > 70:
                        reasons.append("RSI超买")
                    elif features[factor] < 30:
                        reasons.append("RSI超卖")
                elif 'momentum' in factor:
                    if features[factor] > 5:
                        reasons.append(f"{factor}强势上涨")
                    elif features[factor] < -5:
                        reasons.append(f"{factor}弱势下跌")
        
        reason = "动量表现" + ("良好" if score > 0 else "一般") + (f"({', '.join(reasons)})" if reasons else "")
        return score, reason
    
    def calculate_volume_score(self, features: Dict[str, float]) -> Tuple[float, str]:
        """计算成交量得分"""
        volume_factors = ['volume_ratio', 'volume_spike', 'turnover_rate']
        
        score = 0
        reasons = []
        
        for factor in volume_factors:
            if factor in features and factor in self.factor_weights:
                factor_score = features[factor] * self.factor_weights[factor]
                score += factor_score
                
                if factor == 'volume_spike' and features[factor] > 0:
                    reasons.append("成交量突增")
                elif factor == 'volume_ratio' and features[factor] > 2:
                    reasons.append("成交量放大")
                elif factor == 'turnover_rate' and features[factor] > 5:
                    reasons.append("换手率较高")
        
        reason = "成交量" + ("活跃" if score > 0 else "平淡") + (f"({', '.join(reasons)})" if reasons else "")
        return score, reason
    
    def calculate_capital_flow_score(self, features: Dict[str, float]) -> Tuple[float, str]:
        """计算资金流向得分"""
        capital_factors = ['main_inflow_score', 'large_inflow_score', 'capital_strength']
        
        score = 0
        reasons = []
        
        for factor in capital_factors:
            if factor in features and factor in self.factor_weights:
                factor_score = features[factor] * self.factor_weights[factor]
                score += factor_score
                
                if factor == 'main_inflow_score' and features[factor] > 60:
                    reasons.append("主力资金净流入")
                elif factor == 'large_inflow_score' and features[factor] > 60:
                    reasons.append("大单资金净流入")
        
        reason = "资金流向" + ("积极" if score > 0 else "消极") + (f"({', '.join(reasons)})" if reasons else "")
        return score, reason
    
    def calculate_sentiment_score(self, features: Dict[str, float]) -> Tuple[float, str]:
        """计算情绪得分"""
        sentiment_factors = ['news_sentiment_score', 'market_sentiment_score', 'overall_sentiment']
        
        score = 0
        reasons = []
        
        for factor in sentiment_factors:
            if factor in features and factor in self.factor_weights:
                factor_score = features[factor] * self.factor_weights[factor]
                score += factor_score
                
                if factor == 'news_sentiment_score' and features[factor] > 70:
                    reasons.append("新闻情绪积极")
                elif factor == 'market_sentiment_score' and features[factor] > 60:
                    reasons.append("市场情绪乐观")
        
        reason = "市场情绪" + ("乐观" if score > 0 else "谨慎") + (f"({', '.join(reasons)})" if reasons else "")
        return score, reason
    
    def calculate_risk_score(self, features: Dict[str, float]) -> Tuple[float, str]:
        """计算风险得分"""
        risk_factors = ['volatility_20d', 'price_stability']
        
        score = 0
        reasons = []
        
        for factor in risk_factors:
            if factor in features and factor in self.factor_weights:
                factor_score = features[factor] * self.factor_weights[factor]
                score += factor_score
                
                if factor == 'volatility_20d' and features[factor] > 30:
                    reasons.append("波动率较高")
                elif factor == 'price_stability' and features[factor] > 70:
                    reasons.append("价格相对稳定")
        
        reason = "风险水平" + ("较低" if score > 0 else "较高") + (f"({', '.join(reasons)})" if reasons else "")
        return score, reason
    
    def calculate_comprehensive_score(self, features: Dict[str, float]) -> Tuple[float, Dict[str, Tuple[float, str]]]:
        """计算综合得分"""
        # 计算各维度得分
        momentum_score, momentum_reason = self.calculate_momentum_score(features)
        volume_score, volume_reason = self.calculate_volume_score(features)
        capital_score, capital_reason = self.calculate_capital_flow_score(features)
        sentiment_score, sentiment_reason = self.calculate_sentiment_score(features)
        risk_score, risk_reason = self.calculate_risk_score(features)
        
        # 综合得分
        total_score = momentum_score + volume_score + capital_score + sentiment_score + risk_score
        
        # 添加其他因子
        for factor_name, weight in self.factor_weights.items():
            if factor_name in features and factor_name not in [
                'momentum_5d', 'momentum_10d', 'momentum_20d', 'rsi',
                'volume_ratio', 'volume_spike', 'turnover_rate',
                'main_inflow_score', 'large_inflow_score', 'capital_strength',
                'news_sentiment_score', 'market_sentiment_score', 'overall_sentiment',
                'volatility_20d', 'price_stability'
            ]:
                total_score += features[factor_name] * weight
        
        # 得分详情
        score_details = {
            'momentum': (momentum_score, momentum_reason),
            'volume': (volume_score, volume_reason),
            'capital_flow': (capital_score, capital_reason),
            'sentiment': (sentiment_score, sentiment_reason),
            'risk': (risk_score, risk_reason)
        }
        
        return total_score, score_details
    
    def score_stocks(self, all_features: Dict[str, Dict[str, float]]) -> List[Dict]:
        """对所有股票进行打分"""
        logger.info("开始对股票进行打分...")
        
        # 标准化特征
        normalized_features = self.normalize_features(all_features)
        
        scored_stocks = []
        
        for stock_code, features in normalized_features.items():
            try:
                # 计算综合得分
                total_score, score_details = self.calculate_comprehensive_score(features)
                
                # 生成推荐理由
                reasons = []
                for category, (score, reason) in score_details.items():
                    if score > 0:
                        reasons.append(reason)
                
                recommendation_reason = "; ".join(reasons) if reasons else "综合表现一般"
                
                # 获取股票基本信息
                original_features = all_features.get(stock_code, {})
                
                stock_result = {
                    'stock_code': stock_code,
                    'stock_name': original_features.get('stock_name', ''),
                    'current_price': original_features.get('current_price', 0),
                    'change_pct': original_features.get('change_pct', 0),
                    'total_score': total_score,
                    'score_details': score_details,
                    'recommendation_reason': recommendation_reason,
                    'features': original_features
                }
                
                scored_stocks.append(stock_result)
                
            except Exception as e:
                logger.error(f"股票{stock_code}打分失败: {e}")
                continue
        
        # 按得分排序
        scored_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        logger.info(f"股票打分完成，共处理{len(scored_stocks)}只股票")
        return scored_stocks
    
    def get_top_recommendations(self, scored_stocks: List[Dict], top_n: int = 20) -> List[Dict]:
        """获取Top推荐股票"""
        # 过滤条件
        filtered_stocks = []
        
        for stock in scored_stocks:
            # 基本过滤条件
            if (stock['total_score'] > 0 and  # 得分为正
                stock['current_price'] > 0 and  # 价格有效
                abs(stock['change_pct']) < 10):  # 涨跌幅不超过10%
                
                filtered_stocks.append(stock)
        
        # 返回Top N
        top_stocks = filtered_stocks[:top_n]
        
        logger.info(f"筛选出{len(top_stocks)}只推荐股票")
        return top_stocks
    
    def format_recommendation_result(self, top_stocks: List[Dict]) -> List[Dict]:
        """格式化推荐结果"""
        formatted_results = []
        
        for i, stock in enumerate(top_stocks, 1):
            result = {
                'rank': i,
                'stock_code': stock['stock_code'],
                'stock_name': stock['stock_name'],
                'current_price': round(stock['current_price'], 2),
                'change_pct': round(stock['change_pct'], 2),
                'total_score': round(stock['total_score'], 2),
                'recommendation_reason': stock['recommendation_reason'],
                'score_breakdown': {
                    category: round(score, 2) 
                    for category, (score, _) in stock['score_details'].items()
                }
            }
            formatted_results.append(result)
        
        return formatted_results