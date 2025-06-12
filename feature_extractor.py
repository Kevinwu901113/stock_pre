#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征提取模块
功能：构造每只股票的因子特征，例如动量、情绪、主力资金、波动率等
"""

import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logging.warning("TA-Lib未安装，将使用自定义实现")

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logging.warning("pandas-ta未安装，将使用自定义实现")

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """特征提取类 - 负责构造股票因子特征，支持多种时间周期和因子组合"""
    
    def __init__(self, config_path: str = "config.yaml",
                 factor_strategy: str = "default",
                 time_period: str = "medium_term",
                 factor_enable_config_path: str = "factor_enable_config.yaml"):
        """初始化特征提取器
        
        Args:
            config_path: 配置文件路径
            factor_strategy: 因子策略 (default/momentum_focused/capital_flow_focused/conservative)
            time_period: 时间周期 (short_term/medium_term/long_term)
            factor_enable_config_path: 因子启用配置文件路径
        """
        self.config = self._load_config(config_path)
        self.factor_enable_config = self._load_config(factor_enable_config_path)
        
        # 选择因子权重策略
        factor_weights_configs = self.config.get('factor_weights', {})
        self.factor_weights = factor_weights_configs.get(factor_strategy,
                                                        factor_weights_configs.get('default', {}))
        
        # 选择时间周期配置
        time_period_configs = self.config.get('time_periods', {})
        self.time_period_config = time_period_configs.get(time_period,
                                                          time_period_configs.get('medium_term', {}))
        
        # 技术指标参数配置 - 根据时间周期调整
        self.momentum_periods = self.time_period_config.get('momentum_periods', [5, 10, 20])
        self.volatility_period = self.time_period_config.get('volatility_period', 20)
        self.ma_periods = self.time_period_config.get('ma_periods', [5, 10, 20])
        
        # 固定技术指标参数
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bollinger_period = 20
        self.bollinger_std = 2
        
        # 全局设置
        self.global_settings = self.factor_enable_config.get('global_settings', {})
        self.enable_normalization = self.global_settings.get('enable_normalization', True)
        self.missing_data_strategy = self.global_settings.get('missing_data_strategy', 'zero')
        
        logger.info(f"特征提取器初始化完成 - 因子策略: {factor_strategy}, 时间周期: {time_period}")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def calculate_momentum_factor(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算动量因子 - 支持配置化的时间周期"""
        min_required_days = max(self.momentum_periods) + 1
        if hist_data.empty or len(hist_data) < min_required_days:
            # 返回默认值，键名基于配置的周期
            default_result = {f'momentum_{period}d': 0 for period in self.momentum_periods}
            default_result['rsi'] = 50
            return default_result
        
        try:
            # 确保数据按日期排序
            hist_data = hist_data.sort_values('日期')
            closes = hist_data['收盘'].values
            
            result = {}
            
            # 计算配置的动量周期
            for period in self.momentum_periods:
                if len(closes) >= period + 1:
                    momentum = (closes[-1] / closes[-(period+1)] - 1) * 100
                    result[f'momentum_{period}d'] = momentum
                else:
                    result[f'momentum_{period}d'] = 0
            
            # 计算RSI
            rsi = self._calculate_rsi(closes, period=self.rsi_period)
            result['rsi'] = rsi
            
            return result
            
        except Exception as e:
            logger.error(f"计算动量因子失败: {e}")
            # 返回默认值
            default_result = {f'momentum_{period}d': 0 for period in self.momentum_periods}
            default_result['rsi'] = 50
            return default_result
    
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
        """计算波动率因子 - 支持配置化的时间周期"""
        min_required_days = self.volatility_period + 1
        if hist_data.empty or len(hist_data) < min_required_days:
            return {
                f'volatility_{self.volatility_period}d': 0,
                'price_stability': 50
            }
        
        try:
            # 计算收益率
            closes = hist_data['收盘'].values
            returns = np.diff(closes) / closes[:-1]
            
            # 配置周期的波动率
            if len(returns) >= self.volatility_period:
                volatility = np.std(returns[-self.volatility_period:]) * np.sqrt(252) * 100
            else:
                volatility = 0
            
            # 价格稳定性评分 (波动率越低，稳定性越高)
            price_stability = max(0, 100 - volatility)
            
            return {
                f'volatility_{self.volatility_period}d': volatility,
                'price_stability': price_stability
            }
        except Exception as e:
            logger.error(f"计算波动率因子失败: {e}")
            return {
                f'volatility_{self.volatility_period}d': 0,
                'price_stability': 50
            }
    
    def calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算技术指标 - 支持配置化的移动平均线周期"""
        min_required_days = max(self.ma_periods) if self.ma_periods else 20
        if hist_data.empty or len(hist_data) < min_required_days:
            # 返回默认值
            default_result = {f'ma{period}': 0 for period in self.ma_periods}
            default_result.update({'macd': 0, 'bollinger_position': 0.5})
            return default_result
        
        try:
            closes = hist_data['收盘'].values
            result = {}
            
            # 配置的移动平均线
            for period in self.ma_periods:
                if len(closes) >= period:
                    ma_value = np.mean(closes[-period:])
                    result[f'ma{period}'] = ma_value
                else:
                    result[f'ma{period}'] = closes[-1] if len(closes) > 0 else 0
            
            # MACD
            macd = self._calculate_macd(closes)
            result['macd'] = macd
            
            # 布林带位置
            bollinger_position = self._calculate_bollinger_position(closes)
            result['bollinger_position'] = bollinger_position
            
            return result
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            # 返回默认值
            default_result = {f'ma{period}': 0 for period in self.ma_periods}
            default_result.update({'macd': 0, 'bollinger_position': 0.5})
            return default_result
    
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
    
    def calculate_advanced_technical_factors(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算高级技术因子"""
        if hist_data.empty or len(hist_data) < 30:
            return {
                'momentum_5d_new': 0,
                'macd_diff': 0,
                'kdj_golden_cross': 0,
                'ma_slope_5d': 0,
                'ma_slope_10d': 0,
                'volume_ratio_new': 1.0,
                'limit_up_yesterday': 0
            }
        
        try:
            # 确保数据按日期排序
            hist_data = hist_data.sort_values('日期')
            closes = hist_data['收盘'].values
            highs = hist_data['最高'].values
            lows = hist_data['最低'].values
            volumes = hist_data['成交量'].values
            
            result = {}
            
            # 1. 近5日涨跌幅（标准化）
            if len(closes) >= 6:
                momentum_5d = (closes[-1] / closes[-6] - 1) * 100
                # 标准化到0-100区间，0为-10%，100为+10%
                result['momentum_5d_new'] = max(0, min(100, (momentum_5d + 10) * 5))
            else:
                result['momentum_5d_new'] = 50
            
            # 2. MACD差值（MACD - Signal）
            macd_diff = self._calculate_macd_diff(closes)
            result['macd_diff'] = macd_diff
            
            # 3. KDJ金叉信号
            kdj_golden_cross = self._calculate_kdj_golden_cross(highs, lows, closes)
            result['kdj_golden_cross'] = kdj_golden_cross
            
            # 4. 均线斜率
            ma_slope_5d = self._calculate_ma_slope(closes, 5)
            ma_slope_10d = self._calculate_ma_slope(closes, 10)
            result['ma_slope_5d'] = ma_slope_5d
            result['ma_slope_10d'] = ma_slope_10d
            
            # 5. 量比（当前成交量/近期平均成交量）
            volume_ratio = self._calculate_volume_ratio(volumes)
            result['volume_ratio_new'] = volume_ratio
            
            # 6. 前一日涨停状态
            limit_up_yesterday = self._check_limit_up_yesterday(hist_data)
            result['limit_up_yesterday'] = limit_up_yesterday
            
            return result
            
        except Exception as e:
            logger.error(f"计算高级技术因子失败: {e}")
            return {
                'momentum_5d_new': 50,
                'macd_diff': 0,
                'kdj_golden_cross': 0,
                'ma_slope_5d': 0,
                'ma_slope_10d': 0,
                'volume_ratio_new': 1.0,
                'limit_up_yesterday': 0
            }
    
    def _calculate_macd_diff(self, prices: np.ndarray) -> float:
        """计算MACD差值（MACD线 - 信号线）"""
        if len(prices) < 35:  # 需要足够的数据计算MACD
            return 0
        
        try:
            if TALIB_AVAILABLE:
                macd_line, signal_line, _ = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
                if not np.isnan(macd_line[-1]) and not np.isnan(signal_line[-1]):
                    return float(macd_line[-1] - signal_line[-1])
            
            # 自定义实现
            ema12 = self._calculate_ema(prices, 12)
            ema26 = self._calculate_ema(prices, 26)
            macd_line = ema12 - ema26
            
            # 简化的信号线计算
            signal_line = macd_line * 0.8  # 简化处理
            return macd_line - signal_line
            
        except Exception as e:
            logger.error(f"计算MACD差值失败: {e}")
            return 0
    
    def _calculate_kdj_golden_cross(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        """计算KDJ金叉信号"""
        if len(closes) < 14:
            return 0
        
        try:
            if PANDAS_TA_AVAILABLE:
                df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
                kdj = ta.stoch(df['high'], df['low'], df['close'], k=9, d=3)
                if kdj is not None and len(kdj) > 1:
                    k_current = kdj['STOCHk_9_3_3'].iloc[-1]
                    d_current = kdj['STOCHd_9_3_3'].iloc[-1]
                    k_prev = kdj['STOCHk_9_3_3'].iloc[-2]
                    d_prev = kdj['STOCHd_9_3_3'].iloc[-2]
                    
                    # 金叉：K线从下方穿越D线
                    if k_prev <= d_prev and k_current > d_current and k_current < 80:
                        return 100
                    elif k_current > d_current:
                        return 60
                    else:
                        return 20
            
            # 自定义KDJ实现
            period = 9
            if len(closes) < period:
                return 0
            
            # 计算RSV
            high_max = np.max(highs[-period:])
            low_min = np.min(lows[-period:])
            if high_max == low_min:
                return 50
            
            rsv = (closes[-1] - low_min) / (high_max - low_min) * 100
            
            # 简化的K值计算
            k_value = rsv * 0.7 + 30  # 简化处理
            d_value = k_value * 0.8 + 20  # 简化处理
            
            if k_value > d_value and k_value < 80:
                return 80
            elif k_value > d_value:
                return 60
            else:
                return 20
            
        except Exception as e:
            logger.error(f"计算KDJ金叉失败: {e}")
            return 0
    
    def _calculate_ma_slope(self, prices: np.ndarray, period: int) -> float:
        """计算移动平均线斜率"""
        if len(prices) < period + 2:
            return 0
        
        try:
            # 计算最近两个周期的移动平均值
            ma_current = np.mean(prices[-period:])
            ma_previous = np.mean(prices[-(period+1):-1])
            
            # 计算斜率（标准化为百分比）
            slope = (ma_current / ma_previous - 1) * 100
            
            # 标准化到0-100区间
            return max(0, min(100, (slope + 5) * 10))
            
        except Exception as e:
            logger.error(f"计算均线斜率失败: {e}")
            return 50
    
    def _calculate_volume_ratio(self, volumes: np.ndarray) -> float:
        """计算量比"""
        if len(volumes) < 6:
            return 1.0
        
        try:
            # 当前成交量
            current_volume = volumes[-1]
            
            # 前5日平均成交量
            avg_volume = np.mean(volumes[-6:-1])
            
            if avg_volume == 0:
                return 1.0
            
            volume_ratio = current_volume / avg_volume
            
            # 限制在合理范围内
            return max(0.1, min(10.0, volume_ratio))
            
        except Exception as e:
            logger.error(f"计算量比失败: {e}")
            return 1.0
    
    def _check_limit_up_yesterday(self, hist_data: pd.DataFrame) -> float:
        """检查前一日是否涨停"""
        if len(hist_data) < 2:
            return 0
        
        try:
            # 获取前一日数据
            yesterday_data = hist_data.iloc[-2]
            day_before_data = hist_data.iloc[-3] if len(hist_data) >= 3 else yesterday_data
            
            yesterday_close = yesterday_data['收盘']
            day_before_close = day_before_data['收盘']
            
            # 计算涨幅
            change_pct = (yesterday_close / day_before_close - 1) * 100
            
            # 判断是否接近涨停（9.8%以上认为是涨停）
            if change_pct >= 9.8:
                return 100
            elif change_pct >= 7.0:
                return 60  # 大涨
            elif change_pct >= 3.0:
                return 30  # 上涨
            else:
                return 0
                
        except Exception as e:
            logger.error(f"检查涨停状态失败: {e}")
            return 0
    
    def calculate_sector_performance(self, stock_code: str, market_data: Dict) -> float:
        """计算所属行业表现"""
        try:
            # 从市场数据中获取行业信息
            sector_performance = market_data.get('sector_performance', {})
            
            # 根据股票代码判断所属行业（简化处理）
            sector = self._get_stock_sector(stock_code)
            
            if sector in sector_performance:
                performance = sector_performance[sector]
                # 标准化到0-100区间
                return max(0, min(100, (performance + 10) * 5))
            else:
                return 50  # 默认中性
                
        except Exception as e:
            logger.error(f"计算行业表现失败: {e}")
            return 50
    
    def _get_stock_sector(self, stock_code: str) -> str:
        """根据股票代码获取所属行业（简化实现）"""
        # 这里可以接入真实的行业分类数据
        # 简化处理：根据代码前缀判断
        if stock_code.startswith('00'):
            return '主板'
        elif stock_code.startswith('30'):
            return '创业板'
        elif stock_code.startswith('60'):
            return '沪市主板'
        elif stock_code.startswith('688'):
            return '科创板'
        else:
            return '其他'
    
    def calculate_main_capital_inflow(self, capital_flow_data: Dict) -> float:
        """计算主力资金净流入（标准化）"""
        try:
            main_net_inflow = capital_flow_data.get('main_net_inflow', 0)
            main_net_inflow_pct = capital_flow_data.get('main_net_inflow_pct', 0)
            
            # 综合考虑绝对值和百分比
            if main_net_inflow_pct > 0:
                # 净流入
                score = min(100, 50 + main_net_inflow_pct * 10)
            else:
                # 净流出
                score = max(0, 50 + main_net_inflow_pct * 10)
            
            return score
            
        except Exception as e:
            logger.error(f"计算主力资金净流入失败: {e}")
            return 50
    
    def _filter_enabled_factors(self, features: Dict[str, float]) -> Dict[str, float]:
        """根据配置过滤启用的因子"""
        filtered_features = {}
        
        # 获取各类因子的启用配置
        momentum_config = self.factor_enable_config.get('momentum_factors', {})
        volume_config = self.factor_enable_config.get('volume_factors', {})
        capital_config = self.factor_enable_config.get('capital_flow_factors', {})
        technical_config = self.factor_enable_config.get('technical_factors', {})
        sentiment_config = self.factor_enable_config.get('sentiment_factors', {})
        risk_config = self.factor_enable_config.get('risk_factors', {})
        market_config = self.factor_enable_config.get('market_state_factors', {})
        basic_config = self.factor_enable_config.get('basic_factors', {})
        
        # 合并所有配置
        all_configs = {}
        all_configs.update(momentum_config)
        all_configs.update(volume_config)
        all_configs.update(capital_config)
        all_configs.update(technical_config)
        all_configs.update(sentiment_config)
        all_configs.update(risk_config)
        all_configs.update(market_config)
        all_configs.update(basic_config)
        
        # 过滤启用的因子
        for factor_name, factor_value in features.items():
            if all_configs.get(factor_name, True):  # 默认启用
                filtered_features[factor_name] = factor_value
            else:
                logger.debug(f"因子 {factor_name} 已被配置禁用")
        
        return filtered_features
    
    def _normalize_factors(self, features: Dict[str, float]) -> Dict[str, float]:
        """标准化因子值到0-100区间"""
        if not self.enable_normalization:
            return features
        
        normalized_features = {}
        
        for factor_name, factor_value in features.items():
            try:
                # 处理特殊值
                if np.isnan(factor_value) or np.isinf(factor_value):
                    if self.missing_data_strategy == 'zero':
                        normalized_value = 0
                    elif self.missing_data_strategy == 'mean':
                        normalized_value = 50  # 使用中位数
                    else:
                        continue  # 跳过
                else:
                    # 根据因子类型进行不同的标准化
                    normalized_value = self._normalize_single_factor(factor_name, factor_value)
                
                normalized_features[factor_name] = normalized_value
                
            except Exception as e:
                logger.error(f"标准化因子 {factor_name} 失败: {e}")
                # 使用默认值
                if self.missing_data_strategy != 'skip':
                    normalized_features[factor_name] = 50
        
        return normalized_features
    
    def _normalize_single_factor(self, factor_name: str, factor_value: float) -> float:
        """标准化单个因子"""
        # 已经标准化的因子（0-100区间）
        already_normalized = [
            'rsi', 'bollinger_position', 'news_sentiment_score', 
            'market_sentiment_score', 'overall_sentiment', 'price_stability',
            'momentum_5d_new', 'kdj_golden_cross', 'ma_slope_5d', 'ma_slope_10d',
            'limit_up_yesterday', 'sector_performance', 'main_capital_inflow'
        ]
        
        if factor_name in already_normalized:
            return max(0, min(100, factor_value))
        
        # 百分比类因子（-100到100）
        percentage_factors = [
            'momentum_5d', 'momentum_10d', 'momentum_20d', 'change_pct'
        ]
        
        if factor_name in percentage_factors:
            # 转换到0-100区间，-10%对应0，+10%对应100
            return max(0, min(100, (factor_value + 10) * 5))
        
        # 比率类因子（通常在0.1-10之间）
        ratio_factors = ['volume_ratio', 'volume_ratio_new', 'turnover_rate']
        
        if factor_name in ratio_factors:
            # 对数变换后标准化
            if factor_value > 0:
                log_value = np.log(factor_value)
                # 假设正常范围是0.1-10，对应log值-2.3到2.3
                normalized = (log_value + 2.3) / 4.6 * 100
                return max(0, min(100, normalized))
            else:
                return 0
        
        # 波动率类因子（通常0-100）
        if 'volatility' in factor_name:
            return max(0, min(100, factor_value))
        
        # MACD类因子（可能为负值）
        if 'macd' in factor_name:
            # 简单的线性变换
            return max(0, min(100, (factor_value + 1) * 50))
        
        # 其他因子使用默认处理
        if factor_value < 0:
            return max(0, min(100, (factor_value + 10) * 5))
        else:
            return max(0, min(100, factor_value))
    
    def _validate_factors(self, features: Dict[str, float]) -> Dict[str, float]:
        """验证因子有效性"""
        validation_config = self.global_settings.get('factor_validation', {})
        if not validation_config.get('enable', True):
            return features
        
        validated_features = {}
        
        for factor_name, factor_value in features.items():
            # 检查是否为有效数值
            if isinstance(factor_value, (int, float)) and not (np.isnan(factor_value) or np.isinf(factor_value)):
                validated_features[factor_name] = factor_value
            else:
                logger.warning(f"因子 {factor_name} 值无效: {factor_value}")
                if self.missing_data_strategy != 'skip':
                    validated_features[factor_name] = 50  # 默认中性值
        
        return validated_features
     
    def extract_all_features(self, stock_data: Dict, stock_code: str = None) -> Dict[str, float]:
        """提取所有特征"""
        features = {}
        
        try:
            # 获取各部分数据
            hist_data = stock_data.get('history', pd.DataFrame())
            realtime_data = stock_data.get('realtime', {})
            capital_flow_data = stock_data.get('capital_flow', {})
            news_sentiment = stock_data.get('news_sentiment', 0.5)
            market_sentiment = stock_data.get('market_sentiment', {})
            market_data = stock_data.get('market_data', {})
            
            # 计算各类因子
            momentum_features = self.calculate_momentum_factor(hist_data)
            volume_features = self.calculate_volume_factor(hist_data, realtime_data)
            capital_features = self.calculate_capital_flow_factor(capital_flow_data)
            volatility_features = self.calculate_volatility_factor(hist_data)
            technical_features = self.calculate_technical_indicators(hist_data)
            sentiment_features = self.calculate_sentiment_factor(news_sentiment, market_sentiment)
            
            # 新增高级技术因子
            advanced_technical_features = self.calculate_advanced_technical_factors(hist_data)
            
            # 行业表现因子
            if stock_code:
                sector_performance = self.calculate_sector_performance(stock_code, market_data)
                features['sector_performance'] = sector_performance
            
            # 主力资金净流入因子（标准化版本）
            main_capital_inflow = self.calculate_main_capital_inflow(capital_flow_data)
            features['main_capital_inflow'] = main_capital_inflow
            
            # 合并所有特征
            features.update(momentum_features)
            features.update(volume_features)
            features.update(capital_features)
            features.update(volatility_features)
            features.update(technical_features)
            features.update(sentiment_features)
            features.update(advanced_technical_features)
            
            # 添加基础信息
            features.update({
                'current_price': realtime_data.get('price', 0),
                'change_pct': realtime_data.get('change_pct', 0),
                'amplitude': realtime_data.get('amplitude', 0)
            })
            
            # 应用因子处理流程
            features = self._filter_enabled_factors(features)
            features = self._validate_factors(features)
            features = self._normalize_factors(features)
            
        except Exception as e:
            logger.error(f"提取特征失败: {e}")
        
        return features
    
    def batch_extract_features(self, all_stock_data: Dict[str, Dict]) -> Dict[str, Dict[str, float]]:
        """批量提取特征"""
        logger.info("开始批量提取特征...")
        
        all_features = {}
        
        for stock_code, stock_data in all_stock_data.items():
            try:
                features = self.extract_all_features(stock_data, stock_code)
                all_features[stock_code] = features
                logger.debug(f"股票{stock_code}特征提取完成")
            except Exception as e:
                logger.error(f"股票{stock_code}特征提取失败: {e}")
                continue
        
        logger.info(f"特征提取完成，共处理{len(all_features)}只股票")
        return all_features