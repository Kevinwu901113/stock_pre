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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoringEngine:
    """打分引擎类"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "factor_config.yaml"
        self.factor_weights = self.load_factor_config()
        
    def load_factor_config(self) -> Dict[str, float]:
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
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if 'factor_weights' in config:
                        default_weights.update(config['factor_weights'])
                        logger.info(f"从{self.config_path}加载因子配置")
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        else:
            logger.info("配置文件不存在，使用默认因子权重")
            
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
    
    def normalize_features(self, all_features: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """特征标准化"""
        if not all_features:
            return {}
        
        # 获取所有特征名称
        feature_names = set()
        for features in all_features.values():
            feature_names.update(features.keys())
        
        # 计算每个特征的统计信息
        feature_stats = {}
        for feature_name in feature_names:
            values = []
            for features in all_features.values():
                if feature_name in features:
                    value = features[feature_name]
                    # 安全的数值检查
                    if self._is_valid_number(value):
                        values.append(float(value))
            
            if values:
                feature_stats[feature_name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
            else:
                feature_stats[feature_name] = {'mean': 0, 'std': 1, 'min': 0, 'max': 1}
        
        # 标准化特征
        normalized_features = {}
        for stock_code, features in all_features.items():
            normalized_features[stock_code] = {}
            
            for feature_name, value in features.items():
                # 检查是否为有效数值
                if not self._is_valid_number(value):
                    normalized_features[stock_code][feature_name] = 50.0  # 使用中性值
                    continue
                
                # 转换为浮点数
                try:
                    numeric_value = float(value)
                except (ValueError, TypeError):
                    normalized_features[stock_code][feature_name] = 50.0
                    continue
                
                # 获取统计信息
                if feature_name not in feature_stats:
                    normalized_features[stock_code][feature_name] = 50.0
                    continue
                    
                stats = feature_stats[feature_name]
                
                # 使用Z-score标准化，但限制在[-3, 3]范围内
                if stats['std'] > 0:
                    normalized_value = (numeric_value - stats['mean']) / stats['std']
                    normalized_value = max(-3, min(3, normalized_value))
                else:
                    normalized_value = 0
                
                # 转换到[0, 100]范围
                normalized_features[stock_code][feature_name] = (normalized_value + 3) * 100 / 6
        
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

if __name__ == "__main__":
    # 测试代码
    engine = ScoringEngine()
    
    # 创建测试特征数据
    test_features = {
        '000001': {
            'momentum_5d': 3.2, 'momentum_10d': 5.1, 'momentum_20d': 8.3,
            'rsi': 65, 'volume_ratio': 2.5, 'volume_spike': 1,
            'main_inflow_score': 75, 'capital_strength': 68,
            'news_sentiment_score': 72, 'overall_sentiment': 70,
            'volatility_20d': 25, 'current_price': 15.68, 'change_pct': 2.1,
            'stock_name': '平安银行'
        },
        '000002': {
            'momentum_5d': -1.2, 'momentum_10d': 1.1, 'momentum_20d': -2.3,
            'rsi': 45, 'volume_ratio': 1.2, 'volume_spike': 0,
            'main_inflow_score': 45, 'capital_strength': 48,
            'news_sentiment_score': 52, 'overall_sentiment': 50,
            'volatility_20d': 35, 'current_price': 28.45, 'change_pct': -0.8,
            'stock_name': '万科A'
        }
    }
    
    scored_stocks = engine.score_stocks(test_features)
    top_stocks = engine.get_top_recommendations(scored_stocks, 10)
    formatted_results = engine.format_recommendation_result(top_stocks)
    
    print("推荐结果:")
    for result in formatted_results:
        print(f"排名{result['rank']}: {result['stock_name']}({result['stock_code']}) - 得分: {result['total_score']}")
        print(f"  推荐理由: {result['recommendation_reason']}")
        print()