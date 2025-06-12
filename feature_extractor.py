#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征提取模块
功能：构造每只股票的因子特征，例如动量、情绪、主力资金、波动率等
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureExtractor:
    """特征提取类"""
    
    def __init__(self):
        pass
    
    def calculate_momentum_factor(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算动量因子"""
        if hist_data.empty or len(hist_data) < 20:
            return {'momentum_5d': 0, 'momentum_10d': 0, 'momentum_20d': 0, 'rsi': 50}
        
        try:
            # 确保数据按日期排序
            hist_data = hist_data.sort_values('日期')
            closes = hist_data['收盘'].values
            
            # 计算不同周期的动量
            momentum_5d = (closes[-1] / closes[-6] - 1) * 100 if len(closes) >= 6 else 0
            momentum_10d = (closes[-1] / closes[-11] - 1) * 100 if len(closes) >= 11 else 0
            momentum_20d = (closes[-1] / closes[-21] - 1) * 100 if len(closes) >= 21 else 0
            
            # 计算RSI
            rsi = self._calculate_rsi(closes, period=14)
            
            return {
                'momentum_5d': momentum_5d,
                'momentum_10d': momentum_10d,
                'momentum_20d': momentum_20d,
                'rsi': rsi
            }
        except Exception as e:
            logger.error(f"计算动量因子失败: {e}")
            return {'momentum_5d': 0, 'momentum_10d': 0, 'momentum_20d': 0, 'rsi': 50}
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_volume_factor(self, hist_data: pd.DataFrame, realtime_data: Dict) -> Dict[str, float]:
        """计算成交量因子"""
        if hist_data.empty:
            return {'volume_ratio': 1.0, 'volume_spike': 0, 'turnover_rate': 0}
        
        try:
            # 计算成交量比率
            recent_volumes = hist_data['成交量'].tail(5).mean()
            current_volume = realtime_data.get('volume', 0)
            volume_ratio = current_volume / recent_volumes if recent_volumes > 0 else 1.0
            
            # 成交量突增因子
            volume_spike = 1 if volume_ratio > 2.0 else 0
            
            # 换手率
            turnover_rate = realtime_data.get('turnover', 0) / 100000000  # 转换为亿
            
            return {
                'volume_ratio': volume_ratio,
                'volume_spike': volume_spike,
                'turnover_rate': turnover_rate
            }
        except Exception as e:
            logger.error(f"计算成交量因子失败: {e}")
            return {'volume_ratio': 1.0, 'volume_spike': 0, 'turnover_rate': 0}
    
    def calculate_capital_flow_factor(self, capital_flow_data: Dict) -> Dict[str, float]:
        """计算资金流向因子"""
        if not capital_flow_data:
            return {'main_inflow_score': 0, 'large_inflow_score': 0, 'capital_strength': 0}
        
        try:
            # 主力净流入评分
            main_net_inflow = capital_flow_data.get('main_net_inflow', 0)
            main_inflow_pct = capital_flow_data.get('main_net_inflow_pct', 0)
            
            # 大单净流入评分
            large_net_inflow = capital_flow_data.get('large_net_inflow', 0)
            super_large_net_inflow = capital_flow_data.get('super_large_net_inflow', 0)
            
            # 资金流入强度评分 (0-100)
            main_inflow_score = min(max(main_inflow_pct * 10, -50), 50) + 50
            large_inflow_score = 50 + (large_net_inflow + super_large_net_inflow) / 10000000  # 标准化
            
            # 综合资金强度
            capital_strength = (main_inflow_score + large_inflow_score) / 2
            
            return {
                'main_inflow_score': main_inflow_score,
                'large_inflow_score': large_inflow_score,
                'capital_strength': capital_strength
            }
        except Exception as e:
            logger.error(f"计算资金流向因子失败: {e}")
            return {'main_inflow_score': 0, 'large_inflow_score': 0, 'capital_strength': 0}
    
    def calculate_volatility_factor(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算波动率因子"""
        if hist_data.empty or len(hist_data) < 10:
            return {'volatility_10d': 0, 'volatility_20d': 0, 'price_stability': 50}
        
        try:
            # 计算收益率
            closes = hist_data['收盘'].values
            returns = np.diff(closes) / closes[:-1]
            
            # 10日波动率
            volatility_10d = np.std(returns[-10:]) * np.sqrt(252) * 100 if len(returns) >= 10 else 0
            
            # 20日波动率
            volatility_20d = np.std(returns[-20:]) * np.sqrt(252) * 100 if len(returns) >= 20 else 0
            
            # 价格稳定性评分 (波动率越低，稳定性越高)
            price_stability = max(0, 100 - volatility_20d)
            
            return {
                'volatility_10d': volatility_10d,
                'volatility_20d': volatility_20d,
                'price_stability': price_stability
            }
        except Exception as e:
            logger.error(f"计算波动率因子失败: {e}")
            return {'volatility_10d': 0, 'volatility_20d': 0, 'price_stability': 50}
    
    def calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算技术指标"""
        if hist_data.empty or len(hist_data) < 20:
            return {'ma5': 0, 'ma10': 0, 'ma20': 0, 'macd': 0, 'bollinger_position': 0.5}
        
        try:
            closes = hist_data['收盘'].values
            
            # 移动平均线
            ma5 = np.mean(closes[-5:]) if len(closes) >= 5 else closes[-1]
            ma10 = np.mean(closes[-10:]) if len(closes) >= 10 else closes[-1]
            ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else closes[-1]
            
            # MACD
            macd = self._calculate_macd(closes)
            
            # 布林带位置
            bollinger_position = self._calculate_bollinger_position(closes)
            
            return {
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'macd': macd,
                'bollinger_position': bollinger_position
            }
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {'ma5': 0, 'ma10': 0, 'ma20': 0, 'macd': 0, 'bollinger_position': 0.5}
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
        """计算MACD"""
        if len(prices) < slow:
            return 0
        
        # 计算EMA
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        # MACD线
        macd_line = ema_fast - ema_slow
        
        return macd_line
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """计算指数移动平均"""
        if len(prices) < period:
            return np.mean(prices)
        
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def _calculate_bollinger_position(self, prices: np.ndarray, period: int = 20) -> float:
        """计算布林带位置"""
        if len(prices) < period:
            return 0.5
        
        recent_prices = prices[-period:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        current_price = prices[-1]
        upper_band = mean_price + 2 * std_price
        lower_band = mean_price - 2 * std_price
        
        if upper_band == lower_band:
            return 0.5
        
        position = (current_price - lower_band) / (upper_band - lower_band)
        return max(0, min(1, position))
    
    def calculate_sentiment_factor(self, news_sentiment: float, market_sentiment: Dict) -> Dict[str, float]:
        """计算情绪因子"""
        try:
            # 个股新闻情绪评分
            news_score = news_sentiment * 100
            
            # 市场整体情绪评分
            market_up_ratio = market_sentiment.get('up_ratio', 0.5)
            limit_up_count = market_sentiment.get('limit_up_count', 0)
            
            market_score = market_up_ratio * 100
            limit_bonus = min(limit_up_count / 10, 10)  # 涨停数量奖励，最多10分
            
            # 综合情绪评分
            overall_sentiment = (news_score * 0.6 + market_score * 0.4 + limit_bonus)
            
            return {
                'news_sentiment_score': news_score,
                'market_sentiment_score': market_score,
                'overall_sentiment': overall_sentiment
            }
        except Exception as e:
            logger.error(f"计算情绪因子失败: {e}")
            return {'news_sentiment_score': 50, 'market_sentiment_score': 50, 'overall_sentiment': 50}
    
    def extract_all_features(self, stock_data: Dict) -> Dict[str, float]:
        """提取所有特征"""
        features = {}
        
        try:
            # 获取各部分数据
            hist_data = stock_data.get('history', pd.DataFrame())
            realtime_data = stock_data.get('realtime', {})
            capital_flow_data = stock_data.get('capital_flow', {})
            news_sentiment = stock_data.get('news_sentiment', 0.5)
            market_sentiment = stock_data.get('market_sentiment', {})
            
            # 计算各类因子
            momentum_features = self.calculate_momentum_factor(hist_data)
            volume_features = self.calculate_volume_factor(hist_data, realtime_data)
            capital_features = self.calculate_capital_flow_factor(capital_flow_data)
            volatility_features = self.calculate_volatility_factor(hist_data)
            technical_features = self.calculate_technical_indicators(hist_data)
            sentiment_features = self.calculate_sentiment_factor(news_sentiment, market_sentiment)
            
            # 合并所有特征
            features.update(momentum_features)
            features.update(volume_features)
            features.update(capital_features)
            features.update(volatility_features)
            features.update(technical_features)
            features.update(sentiment_features)
            
            # 添加基础信息
            features.update({
                'current_price': realtime_data.get('price', 0),
                'change_pct': realtime_data.get('change_pct', 0),
                'amplitude': realtime_data.get('amplitude', 0)
            })
            
        except Exception as e:
            logger.error(f"提取特征失败: {e}")
        
        return features
    
    def batch_extract_features(self, all_stock_data: Dict[str, Dict]) -> Dict[str, Dict[str, float]]:
        """批量提取特征"""
        logger.info("开始批量提取特征...")
        
        all_features = {}
        
        for stock_code, stock_data in all_stock_data.items():
            try:
                features = self.extract_all_features(stock_data)
                all_features[stock_code] = features
                logger.debug(f"股票{stock_code}特征提取完成")
            except Exception as e:
                logger.error(f"股票{stock_code}特征提取失败: {e}")
                continue
        
        logger.info(f"特征提取完成，共处理{len(all_features)}只股票")
        return all_features

if __name__ == "__main__":
    # 测试代码
    extractor = FeatureExtractor()
    
    # 创建测试数据
    test_hist_data = pd.DataFrame({
        '日期': pd.date_range('2024-01-01', periods=30),
        '收盘': np.random.randn(30).cumsum() + 100,
        '成交量': np.random.randint(1000000, 10000000, 30)
    })
    
    test_realtime_data = {
        'price': 105.5,
        'change_pct': 2.3,
        'volume': 5000000,
        'turnover': 500000000
    }
    
    test_stock_data = {
        'history': test_hist_data,
        'realtime': test_realtime_data,
        'capital_flow': {'main_net_inflow': 10000000, 'main_net_inflow_pct': 5.2},
        'news_sentiment': 0.7,
        'market_sentiment': {'up_ratio': 0.6, 'limit_up_count': 15}
    }
    
    features = extractor.extract_all_features(test_stock_data)
    print("提取的特征:")
    for key, value in features.items():
        print(f"{key}: {value:.2f}")