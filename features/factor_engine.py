#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子引擎模块
负责构造各类量价技术指标、资金因子、市场情绪等特征
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
# import talib  # 暂时注释掉，因为库有问题
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class FactorEngine:
    """
    因子引擎类，用于构造各类股票特征因子
    """
    
    def __init__(self):
        self.factors = {}
        self.factor_groups = {
            'technical': [],  # 技术指标
            'volume': [],     # 成交量指标
            'momentum': [],   # 动量指标
            'volatility': [], # 波动率指标
            'sentiment': [],  # 市场情绪指标
            'fundamental': [] # 基本面指标
        }
    
    def calculate_technical_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标因子
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含技术指标的DataFrame
        """
        result = data.copy()
        
        # 移动平均线 (使用pandas替代talib)
        result['ma5'] = data['close'].rolling(window=5).mean()
        result['ma10'] = data['close'].rolling(window=10).mean()
        result['ma20'] = data['close'].rolling(window=20).mean()
        result['ma60'] = data['close'].rolling(window=60).mean()
        
        # 指数移动平均 (使用pandas替代talib)
        result['ema12'] = data['close'].ewm(span=12).mean()
        result['ema26'] = data['close'].ewm(span=26).mean()
        
        # 暂时注释掉复杂指标，因为talib库有问题
        # # MACD
        # macd, macdsignal, macdhist = talib.MACD(data['close'])
        # result['macd'] = macd
        # result['macd_signal'] = macdsignal
        # result['macd_hist'] = macdhist
        
        # # RSI
        # result['rsi6'] = talib.RSI(data['close'], timeperiod=6)
        # result['rsi14'] = talib.RSI(data['close'], timeperiod=14)
        
        # # 布林带
        # bb_upper, bb_middle, bb_lower = talib.BBANDS(data['close'])
        # result['bb_upper'] = bb_upper
        # result['bb_middle'] = bb_middle
        # result['bb_lower'] = bb_lower
        # result['bb_width'] = (bb_upper - bb_lower) / bb_middle
        # result['bb_position'] = (data['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # # KDJ
        # slowk, slowd = talib.STOCH(data['high'], data['low'], data['close'])
        # result['kdj_k'] = slowk
        # result['kdj_d'] = slowd
        # result['kdj_j'] = 3 * slowk - 2 * slowd
        
        # # 威廉指标
        # result['wr10'] = talib.WILLR(data['high'], data['low'], data['close'], timeperiod=10)
        
        # # CCI
        # result['cci14'] = talib.CCI(data['high'], data['low'], data['close'], timeperiod=14)
        
        # 价格相对位置
        result['price_position_5'] = self._calculate_price_position(data['close'], 5)
        result['price_position_20'] = self._calculate_price_position(data['close'], 20)
        
        self.factor_groups['technical'].extend([
            'ma5', 'ma10', 'ma20', 'ma60', 'ema12', 'ema26',
            'macd', 'macd_signal', 'macd_hist', 'rsi6', 'rsi14',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            'kdj_k', 'kdj_d', 'kdj_j', 'wr10', 'cci14',
            'price_position_5', 'price_position_20'
        ])
        
        return result
    
    def calculate_volume_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算成交量相关因子
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含成交量因子的DataFrame
        """
        result = data.copy()
        
        # 成交量移动平均 (使用pandas替代talib)
        result['vol_ma5'] = data['volume'].rolling(window=5).mean()
        result['vol_ma10'] = data['volume'].rolling(window=10).mean()
        result['vol_ma20'] = data['volume'].rolling(window=20).mean()
        
        # 量比
        result['volume_ratio'] = data['volume'] / result['vol_ma5']
        
        # 暂时注释掉复杂的成交量指标
        # # 成交量相对强度
        # result['vol_rsi'] = talib.RSI(data['volume'], timeperiod=14)
        
        # # OBV
        # result['obv'] = talib.OBV(data['close'], data['volume'])
        
        # # 资金流向指标
        # result['mfi'] = talib.MFI(data['high'], data['low'], data['close'], data['volume'])
        
        # 成交量价格趋势
        result['vpt'] = self._calculate_vpt(data)
        
        # 换手率（需要流通股本数据）
        if 'float_shares' in data.columns:
            result['turnover_rate'] = data['volume'] / data['float_shares'] * 100
        
        # 量价背离度
        result['price_volume_divergence'] = self._calculate_price_volume_divergence(data)
        
        self.factor_groups['volume'].extend([
            'vol_ma5', 'vol_ma10', 'vol_ma20', 'volume_ratio',
            'vol_rsi', 'obv', 'mfi', 'vpt', 'price_volume_divergence'
        ])
        
        if 'turnover_rate' in result.columns:
            self.factor_groups['volume'].append('turnover_rate')
        
        return result
    
    def calculate_momentum_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算动量因子
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含动量因子的DataFrame
        """
        result = data.copy()
        
        # 价格动量
        result['momentum_5'] = data['close'] / data['close'].shift(5) - 1
        result['momentum_10'] = data['close'] / data['close'].shift(10) - 1
        result['momentum_20'] = data['close'] / data['close'].shift(20) - 1
        result['momentum_60'] = data['close'] / data['close'].shift(60) - 1
        
        # ROC (使用pandas替代talib)
        result['roc_5'] = data['close'].pct_change(periods=5) * 100
        result['roc_10'] = data['close'].pct_change(periods=10) * 100
        result['roc_20'] = data['close'].pct_change(periods=20) * 100
        
        # 相对强度
        result['rs_5'] = self._calculate_relative_strength(data['close'], 5)
        result['rs_20'] = self._calculate_relative_strength(data['close'], 20)
        
        # 动量加速度
        result['momentum_acceleration'] = result['momentum_5'] - result['momentum_10']
        
        # 趋势强度
        result['trend_strength'] = self._calculate_trend_strength(data['close'])
        
        self.factor_groups['momentum'].extend([
            'momentum_5', 'momentum_10', 'momentum_20', 'momentum_60',
            'roc_5', 'roc_10', 'roc_20', 'rs_5', 'rs_20',
            'momentum_acceleration', 'trend_strength'
        ])
        
        return result
    
    def calculate_volatility_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算波动率因子
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含波动率因子的DataFrame
        """
        result = data.copy()
        
        # 收益率
        returns = data['close'].pct_change()
        
        # 历史波动率
        result['volatility_5'] = returns.rolling(5).std() * np.sqrt(252)
        result['volatility_10'] = returns.rolling(10).std() * np.sqrt(252)
        result['volatility_20'] = returns.rolling(20).std() * np.sqrt(252)
        result['volatility_60'] = returns.rolling(60).std() * np.sqrt(252)
        
        # 暂时注释掉ATR指标，因为talib库有问题
        # # ATR
        # result['atr_14'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
        # result['atr_20'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=20)
        
        # # 真实波动幅度
        # result['true_range'] = talib.TRANGE(data['high'], data['low'], data['close'])
        
        # 简单的波动幅度计算
        result['high_low_range'] = data['high'] - data['low']
        
        # 波动率比率
        result['volatility_ratio'] = result['volatility_5'] / result['volatility_20']
        
        # 价格振幅
        result['price_amplitude'] = (data['high'] - data['low']) / data['close']
        
        # 上下影线比率
        result['upper_shadow'] = (data['high'] - np.maximum(data['open'], data['close'])) / data['close']
        result['lower_shadow'] = (np.minimum(data['open'], data['close']) - data['low']) / data['close']
        result['shadow_ratio'] = result['upper_shadow'] / (result['lower_shadow'] + 1e-8)
        
        self.factor_groups['volatility'].extend([
            'volatility_5', 'volatility_10', 'volatility_20', 'volatility_60',
            'atr_14', 'atr_20', 'true_range', 'volatility_ratio',
            'price_amplitude', 'upper_shadow', 'lower_shadow', 'shadow_ratio'
        ])
        
        return result
    
    def calculate_sentiment_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算市场情绪因子
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含情绪因子的DataFrame
        """
        result = data.copy()
        
        # 涨跌停统计
        if 'limit_up' in data.columns and 'limit_down' in data.columns:
            result['limit_up_ratio'] = data['limit_up'].rolling(5).mean()
            result['limit_down_ratio'] = data['limit_down'].rolling(5).mean()
        
        # 振幅分布
        amplitude = (data['high'] - data['low']) / data['close']
        result['amplitude_percentile'] = amplitude.rolling(20).rank(pct=True)
        
        # 成交量异常度
        vol_mean = data['volume'].rolling(20).mean()
        vol_std = data['volume'].rolling(20).std()
        result['volume_anomaly'] = (data['volume'] - vol_mean) / (vol_std + 1e-8)
        
        # 价格跳空
        result['gap_up'] = (data['open'] > data['close'].shift(1)).astype(int)
        result['gap_down'] = (data['open'] < data['close'].shift(1)).astype(int)
        result['gap_ratio'] = abs(data['open'] - data['close'].shift(1)) / data['close'].shift(1)
        
        # 连续涨跌天数
        returns = data['close'].pct_change()
        result['consecutive_up'] = self._calculate_consecutive_days(returns > 0)
        result['consecutive_down'] = self._calculate_consecutive_days(returns < 0)
        
        # 市场强度指标
        result['market_strength'] = self._calculate_market_strength(data)
        
        sentiment_factors = [
            'amplitude_percentile', 'volume_anomaly', 'gap_up', 'gap_down',
            'gap_ratio', 'consecutive_up', 'consecutive_down', 'market_strength'
        ]
        
        if 'limit_up_ratio' in result.columns:
            sentiment_factors.extend(['limit_up_ratio', 'limit_down_ratio'])
        
        self.factor_groups['sentiment'].extend(sentiment_factors)
        
        return result
    
    def calculate_all_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有因子
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含所有因子的DataFrame
        """
        result = data.copy()
        
        # 依次计算各类因子
        result = self.calculate_technical_factors(result)
        result = self.calculate_volume_factors(result)
        result = self.calculate_momentum_factors(result)
        result = self.calculate_volatility_factors(result)
        result = self.calculate_sentiment_factors(result)
        
        return result
    
    def get_factor_names(self, group: Optional[str] = None) -> List[str]:
        """
        获取因子名称列表
        
        Args:
            group: 因子组名，如果为None则返回所有因子
            
        Returns:
            因子名称列表
        """
        if group is None:
            all_factors = []
            for factors in self.factor_groups.values():
                all_factors.extend(factors)
            return all_factors
        else:
            return self.factor_groups.get(group, [])
    
    def _calculate_price_position(self, prices: pd.Series, window: int) -> pd.Series:
        """
        计算价格在指定窗口内的相对位置
        """
        rolling_min = prices.rolling(window).min()
        rolling_max = prices.rolling(window).max()
        return (prices - rolling_min) / (rolling_max - rolling_min + 1e-8)
    
    def _calculate_vpt(self, data: pd.DataFrame) -> pd.Series:
        """
        计算成交量价格趋势指标
        """
        price_change = data['close'].pct_change()
        vpt = (price_change * data['volume']).cumsum()
        return vpt
    
    def _calculate_price_volume_divergence(self, data: pd.DataFrame) -> pd.Series:
        """
        计算量价背离度
        """
        price_momentum = data['close'].pct_change(5)
        volume_momentum = data['volume'].pct_change(5)
        
        # 计算相关系数
        correlation = price_momentum.rolling(20).corr(volume_momentum)
        return -correlation  # 负相关表示背离
    
    def _calculate_relative_strength(self, prices: pd.Series, window: int) -> pd.Series:
        """
        计算相对强度
        """
        gains = prices.diff().where(prices.diff() > 0, 0)
        losses = -prices.diff().where(prices.diff() < 0, 0)
        
        avg_gains = gains.rolling(window).mean()
        avg_losses = losses.rolling(window).mean()
        
        rs = avg_gains / (avg_losses + 1e-8)
        return rs
    
    def _calculate_trend_strength(self, prices: pd.Series) -> pd.Series:
        """
        计算趋势强度
        """
        # 使用线性回归斜率衡量趋势强度
        def calc_slope(x):
            if len(x) < 2:
                return 0
            y = np.arange(len(x))
            slope, _, r_value, _, _ = stats.linregress(y, x)
            return slope * r_value ** 2  # 斜率乘以R方
        
        return prices.rolling(20).apply(calc_slope)
    
    def _calculate_consecutive_days(self, condition: pd.Series) -> pd.Series:
        """
        计算连续满足条件的天数
        """
        groups = (condition != condition.shift()).cumsum()
        consecutive = condition.groupby(groups).cumsum()
        return consecutive.where(condition, 0)
    
    def _calculate_market_strength(self, data: pd.DataFrame) -> pd.Series:
        """
        计算市场强度指标
        """
        # 综合价格、成交量、波动率的强度指标
        price_strength = data['close'].pct_change(5)
        volume_strength = (data['volume'] / data['volume'].rolling(20).mean() - 1)
        volatility = data['close'].pct_change().rolling(5).std()
        
        # 标准化后加权合成
        price_norm = (price_strength - price_strength.rolling(60).mean()) / price_strength.rolling(60).std()
        volume_norm = (volume_strength - volume_strength.rolling(60).mean()) / volume_strength.rolling(60).std()
        vol_norm = (volatility - volatility.rolling(60).mean()) / volatility.rolling(60).std()
        
        market_strength = 0.5 * price_norm + 0.3 * volume_norm - 0.2 * vol_norm
        return market_strength


def create_factor_engine() -> FactorEngine:
    """
    创建因子引擎实例
    
    Returns:
        FactorEngine实例
    """
    return FactorEngine()