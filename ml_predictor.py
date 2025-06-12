# -*- coding: utf-8 -*-
"""
机器学习预测模块
功能：基于历史数据训练LightGBM模型，预测次日开盘涨跌
"""

import os
import sys
import pandas as pd
import numpy as np
import akshare as ak
import lightgbm as lgb
import pickle
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import DataFetcher
from feature_extractor import FeatureExtractor
from cache_manager import CacheManager

logger = logging.getLogger(__name__)

class MLPredictor:
    """机器学习预测器 - 基于LightGBM的二分类模型"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化ML预测器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化依赖模块
        self.data_fetcher = DataFetcher(config_path)
        self.feature_extractor = FeatureExtractor(config_path)
        self.cache_manager = CacheManager()
        
        # 模型相关配置
        self.model_config = self.config.get('ml_model', {})
        self.model_path = self.model_config.get('model_path', 'models/lightgbm_model.pkl')
        self.scaler_path = self.model_config.get('scaler_path', 'models/scaler.pkl')
        self.feature_names_path = self.model_config.get('feature_names_path', 'models/feature_names.pkl')
        
        # 确保模型目录存在
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # 模型和预处理器
        self.model = None
        self.scaler = None
        self.feature_names = None
        
        # 训练参数
        self.lgb_params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        # 更新参数
        self.lgb_params.update(self.model_config.get('lgb_params', {}))
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def generate_training_samples(self, 
                                start_date: str = None, 
                                end_date: str = None,
                                stock_codes: List[str] = None,
                                min_samples_per_stock: int = 30) -> Tuple[pd.DataFrame, pd.Series]:
        """
        生成训练样本
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            stock_codes: 股票代码列表，如果为None则获取全部股票
            min_samples_per_stock: 每只股票最少样本数
            
        Returns:
            features: 特征DataFrame
            labels: 标签Series (1表示次日开盘上涨，0表示下跌)
        """
        logger.info("开始生成训练样本...")
        
        # 设置默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
            
        # 获取股票列表
        if stock_codes is None:
            stock_codes = self._get_stock_universe()
            
        logger.info(f"处理股票数量: {len(stock_codes)}, 日期范围: {start_date} 到 {end_date}")
        
        all_features = []
        all_labels = []
        
        for i, stock_code in enumerate(stock_codes):
            if i % 50 == 0:
                logger.info(f"处理进度: {i+1}/{len(stock_codes)}")
                
            try:
                # 获取股票历史数据
                stock_data = self._get_stock_historical_data(stock_code, start_date, end_date)
                
                if stock_data is None or len(stock_data) < min_samples_per_stock:
                    continue
                    
                # 处理数据质量问题
                stock_data = self._clean_stock_data(stock_data)
                
                if len(stock_data) < min_samples_per_stock:
                    continue
                    
                # 提取特征 - 只提取最新一天的特征
                features = self._extract_features_for_training(stock_data)
                
                # 构造标签 (次日开盘是否高于今日收盘)
                labels = self._create_labels(stock_data)
                
                # 为每个有效的标签创建特征样本
                for i, label in enumerate(labels):
                    if i < len(stock_data) - 1:  # 确保有次日数据
                        # 提取第i天的特征
                        day_data = stock_data.iloc[:i+1]  # 包含到第i天的历史数据
                        if len(day_data) >= 20:  # 确保有足够的历史数据
                            day_features = self._extract_features_for_training(day_data)
                            if day_features:
                                # 添加股票代码
                                day_features['stock_code'] = stock_code
                                all_features.append(day_features)
                                all_labels.append(label)
                    
            except Exception as e:
                logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
                
        if not all_features:
            raise ValueError("没有生成任何有效的训练样本")
            
        # 将字典列表转换为DataFrame
        features_df = pd.DataFrame(all_features)
        labels_series = pd.Series(all_labels)
        
        # 处理股票代码列
        if 'stock_code' in features_df.columns:
            features_df = features_df.drop('stock_code', axis=1)
        
        # 确保所有特征都是数值型
        for col in features_df.columns:
            features_df[col] = pd.to_numeric(features_df[col], errors='coerce')
        
        # 填充缺失值
        features_df = features_df.fillna(0)
        
        logger.info(f"生成训练样本完成，总样本数: {len(features_df)}, 正样本比例: {labels_series.mean():.3f}")
        
        return features_df, labels_series
    
    def _get_stock_universe(self) -> List[str]:
        """获取股票池"""
        try:
            # 获取A股列表
            stock_list = ak.stock_info_a_code_name()
            # 过滤掉ST股票和科创板
            stock_codes = []
            for _, row in stock_list.iterrows():
                code = row['code']
                name = row['name']
                # 排除ST股票、科创板(688)、创业板(300)
                if ('ST' not in name and 'st' not in name and 
                    not code.startswith('688') and not code.startswith('300')):
                    stock_codes.append(code)
            
            # 限制数量以避免过长的训练时间
            max_stocks = self.model_config.get('max_training_stocks', 500)
            return stock_codes[:max_stocks]
            
        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
            return []
    
    def _get_stock_historical_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        try:
            # 使用缓存
            cache_key = f"hist_{stock_code}_{start_date}_{end_date}"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                return cached_data
                
            # 获取历史行情数据
            hist_data = ak.stock_zh_a_hist(symbol=stock_code, 
                                         start_date=start_date.replace('-', ''), 
                                         end_date=end_date.replace('-', ''),
                                         adjust="qfq")  # 前复权
            
            if hist_data is None or len(hist_data) == 0:
                return None
                
            # 检查并重命名列
            expected_columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'change_pct', 'change_amount', 'turnover_rate']
            
            if len(hist_data.columns) != len(expected_columns):
                # 如果列数不匹配，使用原始列名
                logger.warning(f"股票 {stock_code} 数据列数不匹配，实际: {len(hist_data.columns)}, 期望: {len(expected_columns)}")
                logger.warning(f"实际列名: {list(hist_data.columns)}")
                
                # 尝试使用标准列名映射
                column_mapping = {
                    '日期': 'date',
                    '开盘': 'open', 
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low', 
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'change_pct',
                    '涨跌额': 'change_amount',
                    '换手率': 'turnover_rate'
                }
                
                # 重命名存在的列
                for old_name, new_name in column_mapping.items():
                    if old_name in hist_data.columns:
                        hist_data = hist_data.rename(columns={old_name: new_name})
                
                # 确保必需的列存在
                required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
                missing_columns = [col for col in required_columns if col not in hist_data.columns]
                
                if missing_columns:
                    logger.warning(f"股票 {stock_code} 缺少必需列: {missing_columns}")
                    return None
                    
            else:
                # 列数匹配，直接重命名
                hist_data.columns = expected_columns
            
            # 确保日期列格式正确
            hist_data['date'] = pd.to_datetime(hist_data['date'])
            hist_data = hist_data.sort_values('date').reset_index(drop=True)
            
            # 填充缺失的列
            for col in expected_columns:
                if col not in hist_data.columns:
                    if col in ['amplitude', 'change_pct', 'change_amount', 'turnover_rate']:
                        hist_data[col] = 0.0  # 填充默认值
                    elif col == 'amount':
                        hist_data[col] = hist_data['volume'] * hist_data['close']  # 估算成交额
            
            # 缓存数据
            self.cache_manager.set(cache_key, hist_data, expire_minutes=60)
            
            return hist_data
            
        except Exception as e:
            logger.warning(f"获取股票 {stock_code} 历史数据失败: {e}")
            return None
    
    def _clean_stock_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """清洗股票数据"""
        # 删除缺失值
        data = data.dropna()
        
        # 删除异常值 (涨跌幅超过20%的数据，可能是停牌复牌等异常情况)
        data = data[abs(data['change_pct']) <= 20]
        
        # 删除成交量为0的数据 (停牌)
        data = data[data['volume'] > 0]
        
        # 删除价格异常的数据
        data = data[(data['open'] > 0) & (data['close'] > 0) & 
                   (data['high'] > 0) & (data['low'] > 0)]
        
        # 删除价格逻辑错误的数据
        data = data[(data['high'] >= data['low']) & 
                   (data['high'] >= data['open']) & 
                   (data['high'] >= data['close']) &
                   (data['low'] <= data['open']) & 
                   (data['low'] <= data['close'])]
        
        return data.reset_index(drop=True)
    
    def _extract_features_for_training(self, stock_data: pd.DataFrame) -> Dict[str, float]:
        """为训练提取特征"""
        # 使用现有的特征提取器
        features = self.feature_extractor.extract_all_features({
            'history': stock_data,
            'realtime': {},
            'capital_flow': {},
            'news_sentiment': 0.5,
            'market_sentiment': {},
            'market_data': {}
        })
        
        # 添加一些额外的技术指标特征
        additional_features = self._add_technical_features(stock_data)
        features.update(additional_features)
        
        return features
    
    def _add_technical_features(self, stock_data: pd.DataFrame) -> Dict[str, float]:
        """添加技术指标特征"""
        features = {}
        try:
            if len(stock_data) < 20:
                return features
                
            # 移动平均线
            stock_data = stock_data.copy()
            stock_data['ma5'] = stock_data['close'].rolling(5).mean()
            stock_data['ma10'] = stock_data['close'].rolling(10).mean()
            stock_data['ma20'] = stock_data['close'].rolling(20).mean()
            
            # 获取最新值
            latest = stock_data.iloc[-1]
            
            # 价格相对位置
            if not pd.isna(latest['ma5']) and latest['ma5'] != 0:
                features['price_vs_ma5'] = (latest['close'] - latest['ma5']) / latest['ma5']
            if not pd.isna(latest['ma10']) and latest['ma10'] != 0:
                features['price_vs_ma10'] = (latest['close'] - latest['ma10']) / latest['ma10']
            if not pd.isna(latest['ma20']) and latest['ma20'] != 0:
                features['price_vs_ma20'] = (latest['close'] - latest['ma20']) / latest['ma20']
            
            # 成交量相对强度
            stock_data['volume_ma5'] = stock_data['volume'].rolling(5).mean()
            if not pd.isna(latest['volume']) and not pd.isna(stock_data.iloc[-1]['volume_ma5']) and stock_data.iloc[-1]['volume_ma5'] != 0:
                features['volume_ratio_5d'] = latest['volume'] / stock_data.iloc[-1]['volume_ma5']
            
            # 价格波动率
            volatility_5d = stock_data['close'].pct_change().rolling(5).std().iloc[-1]
            volatility_10d = stock_data['close'].pct_change().rolling(10).std().iloc[-1]
            if not pd.isna(volatility_5d):
                features['volatility_5d'] = volatility_5d
            if not pd.isna(volatility_10d):
                features['volatility_10d'] = volatility_10d
            
            # 高低价差
            if latest['close'] != 0:
                features['hl_ratio'] = (latest['high'] - latest['low']) / latest['close']
            
            # 开盘价相对位置
            if latest['high'] != latest['low']:
                features['open_position'] = (latest['open'] - latest['low']) / (latest['high'] - latest['low'])
                features['close_position'] = (latest['close'] - latest['low']) / (latest['high'] - latest['low'])
            
        except Exception as e:
            logger.warning(f"添加技术特征时出错: {e}")
            
        return features
    
    def _create_labels(self, stock_data: pd.DataFrame) -> List[int]:
        """创建标签：次日开盘是否高于今日收盘"""
        labels = []
        
        for i in range(len(stock_data) - 1):
            today_close = stock_data.iloc[i]['close']
            tomorrow_open = stock_data.iloc[i + 1]['open']
            
            # 1表示次日开盘上涨，0表示下跌或持平
            label = 1 if tomorrow_open > today_close else 0
            labels.append(label)
            
        return labels
    

    
    def train_model(self, 
                   features: pd.DataFrame, 
                   labels: pd.Series,
                   test_size: float = 0.2,
                   n_splits: int = 5) -> Dict:
        """
        训练LightGBM模型
        
        Args:
            features: 特征数据
            labels: 标签数据
            test_size: 测试集比例
            n_splits: 时间序列交叉验证折数
            
        Returns:
            训练结果字典
        """
        logger.info("开始训练模型...")
        
        # 准备特征
        X = features.copy()
        feature_cols = list(X.columns)
        y = labels
        
        # 保存特征名称
        self.feature_names = feature_cols
        
        # 数据标准化
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=feature_cols)
        
        # 时间序列分割
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        cv_scores = []
        feature_importance = np.zeros(len(feature_cols))
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled)):
            logger.info(f"训练第 {fold + 1}/{n_splits} 折...")
            
            X_train, X_val = X_scaled.iloc[train_idx], X_scaled.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # 创建LightGBM数据集
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            # 训练模型
            model = lgb.train(
                self.lgb_params,
                train_data,
                valid_sets=[val_data],
                num_boost_round=1000,
                callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
            )
            
            # 预测和评估
            y_pred_proba = model.predict(X_val)
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            # 计算指标
            accuracy = accuracy_score(y_val, y_pred)
            precision = precision_score(y_val, y_pred)
            recall = recall_score(y_val, y_pred)
            f1 = f1_score(y_val, y_pred)
            auc = roc_auc_score(y_val, y_pred_proba)
            
            cv_scores.append({
                'fold': fold + 1,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'auc': auc
            })
            
            # 累积特征重要性
            feature_importance += model.feature_importance(importance_type='gain')
            
            logger.info(f"第 {fold + 1} 折结果 - AUC: {auc:.4f}, Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        
        # 使用全部数据训练最终模型
        logger.info("使用全部数据训练最终模型...")
        train_data = lgb.Dataset(X_scaled, label=y)
        self.model = lgb.train(
            self.lgb_params,
            train_data,
            num_boost_round=1000
        )
        
        # 保存模型和预处理器
        self._save_model()
        
        # 计算平均性能
        avg_scores = {}
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'auc']:
            scores = [score[metric] for score in cv_scores]
            avg_scores[f'avg_{metric}'] = np.mean(scores)
            avg_scores[f'std_{metric}'] = np.std(scores)
        
        # 特征重要性
        feature_importance = feature_importance / n_splits
        feature_importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        result = {
            'cv_scores': cv_scores,
            'avg_scores': avg_scores,
            'feature_importance': feature_importance_df,
            'n_samples': len(X),
            'n_features': len(feature_cols),
            'positive_rate': y.mean()
        }
        
        logger.info(f"模型训练完成 - 平均AUC: {avg_scores['avg_auc']:.4f} ± {avg_scores['std_auc']:.4f}")
        
        return result
    
    def _save_model(self):
        """保存模型和预处理器"""
        try:
            # 保存模型
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
                
            # 保存标准化器
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
                
            # 保存特征名称
            with open(self.feature_names_path, 'wb') as f:
                pickle.dump(self.feature_names, f)
                
            logger.info(f"模型已保存到: {self.model_path}")
            
        except Exception as e:
            logger.error(f"保存模型失败: {e}")
    
    def load_model(self) -> bool:
        """加载已训练的模型"""
        try:
            # 检查文件是否存在
            if not all(os.path.exists(path) for path in [self.model_path, self.scaler_path, self.feature_names_path]):
                logger.warning("模型文件不存在，需要先训练模型")
                return False
                
            # 加载模型
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
                
            # 加载标准化器
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
                
            # 加载特征名称
            with open(self.feature_names_path, 'rb') as f:
                self.feature_names = pickle.load(f)
                
            logger.info("模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    def predict_today_updown(self, stock_codes: List[str] = None) -> Dict[str, float]:
        """
        预测今日股票次日开盘涨跌概率
        
        Args:
            stock_codes: 股票代码列表，如果为None则预测全部股票
            
        Returns:
            股票代码到上涨概率的字典
        """
        if self.model is None:
            if not self.load_model():
                raise ValueError("模型未训练或加载失败，请先训练模型")
        
        logger.info("开始预测股票次日涨跌...")
        
        # 获取股票列表
        if stock_codes is None:
            stock_codes = self._get_stock_universe()
        
        predictions = {}
        
        for stock_code in stock_codes:
            try:
                # 获取最新数据
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
                
                stock_data = self._get_stock_historical_data(stock_code, start_date, end_date)
                
                if stock_data is None or len(stock_data) < 20:
                    continue
                    
                # 清洗数据
                stock_data = self._clean_stock_data(stock_data)
                
                if len(stock_data) < 20:
                    continue
                    
                # 提取特征
                features = self._extract_features_for_training(stock_data)
                
                if not features:
                    continue
                    
                # 转换为DataFrame并选择模型特征
                features_df = pd.DataFrame([features])
                
                # 确保特征顺序与训练时一致
                missing_features = set(self.feature_names) - set(features_df.columns)
                for feature in missing_features:
                    features_df[feature] = 0
                    
                latest_features = features_df[self.feature_names]
                
                # 检查是否有缺失值
                if latest_features.isnull().any().any():
                    latest_features = latest_features.fillna(0)
                    
                # 标准化
                latest_features_scaled = self.scaler.transform(latest_features)
                
                # 预测
                prob = self.model.predict(latest_features_scaled)[0]
                predictions[stock_code] = float(prob)
                
            except Exception as e:
                logger.warning(f"预测股票 {stock_code} 时出错: {e}")
                continue
        
        logger.info(f"预测完成，成功预测 {len(predictions)} 只股票")
        
        # 按概率排序
        sorted_predictions = dict(sorted(predictions.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_predictions


if __name__ == "__main__":
    # 示例用法
    predictor = MLPredictor()
    
    # 生成训练样本
    features, labels = predictor.generate_training_samples(
        start_date='2022-01-01',
        end_date='2024-01-01'
    )
    
    # 训练模型
    result = predictor.train_model(features, labels)
    print("训练结果:", result['avg_scores'])
    
    # 预测
    predictions = predictor.predict_today_updown(['000001', '000002', '600000'])
    print("预测结果:", predictions)