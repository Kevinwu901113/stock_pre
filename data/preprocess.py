#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据预处理模块
负责对数据进行清洗、缺失值处理、时间对齐、格式统一、构造时间序列结构等
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import logging
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import warnings
import os
import json

warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockDataPreprocessor:
    """A股数据预处理器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化预处理器
        
        Args:
            config: 预处理配置，包含各种预处理参数
        """
        self.config = config or {}
        
        # 标准列名映射
        self.standard_columns = {
            'stock_daily': ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'symbol'],
            'index_daily': ['date', 'open', 'high', 'low', 'close', 'volume', 'index_code'],
            'money_flow': ['date', 'main_net_inflow', 'main_net_inflow_rate', 'symbol'],
            'financial': ['report_date', 'symbol', 'eps', 'roe', 'net_profit', 'revenue']
        }
        
        # 支持的日期格式
        self.date_formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d']
        
        # 异常值处理参数
        self.outlier_std_threshold = self.config.get('outlier_std_threshold', 3.0)  # 3σ原则
        
        # 缺失值处理默认方法
        self.default_missing_method = self.config.get('default_missing_method', 'forward_fill')
    
    def standardize_date_format(self, df: pd.DataFrame, date_column: str = 'date') -> pd.DataFrame:
        """标准化日期格式"""
        if df.empty or date_column not in df.columns:
            return df
        
        df = df.copy()
        
        try:
            # 尝试不同的日期格式
            for fmt in self.date_formats:
                try:
                    df[date_column] = pd.to_datetime(df[date_column], format=fmt)
                    break
                except:
                    continue
            else:
                # 如果所有格式都失败，使用pandas的自动推断
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # 移除无效日期
            df = df.dropna(subset=[date_column])
            
            # 标准化为YYYY-MM-DD格式
            df[date_column] = df[date_column].dt.strftime('%Y-%m-%d')
            df[date_column] = pd.to_datetime(df[date_column])
            
            logger.info(f"日期格式标准化完成，有效记录数: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"日期格式标准化失败: {str(e)}")
            return df
    
    def clean_numeric_data(self, df: pd.DataFrame, numeric_columns: List[str] = None, 
                          outlier_method: str = 'std', replace_with: str = 'nan') -> pd.DataFrame:
        """清洗数值数据"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 如果未指定数值列，则自动检测
        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_columns:
            if col in df.columns:
                # 转换为数值类型
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 移除异常值
                if outlier_method == 'std':
                    # 使用标准差方法（3σ原则）
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    if not pd.isna(mean_val) and not pd.isna(std_val) and std_val > 0:
                        lower_bound = mean_val - self.outlier_std_threshold * std_val
                        upper_bound = mean_val + self.outlier_std_threshold * std_val
                        
                        # 根据设置替换异常值
                        if replace_with == 'nan':
                            df.loc[(df[col] < lower_bound) | (df[col] > upper_bound), col] = np.nan
                        elif replace_with == 'boundary':
                            df.loc[df[col] < lower_bound, col] = lower_bound
                            df.loc[df[col] > upper_bound, col] = upper_bound
                
                elif outlier_method == 'iqr':
                    # 使用四分位距法
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # 根据设置替换异常值
                    if replace_with == 'nan':
                        df.loc[(df[col] < lower_bound) | (df[col] > upper_bound), col] = np.nan
                    elif replace_with == 'boundary':
                        df.loc[df[col] < lower_bound, col] = lower_bound
                        df.loc[df[col] > upper_bound, col] = upper_bound
        
        logger.info(f"数值数据清洗完成，方法: {outlier_method}")
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, method: str = None, 
                            fill_value: Dict[str, Any] = None) -> pd.DataFrame:
        """处理缺失值"""
        if df.empty:
            return df
        
        df = df.copy()
        method = method or self.default_missing_method
        
        if method == 'forward_fill':
            # 前向填充
            df = df.fillna(method='ffill')
        elif method == 'backward_fill':
            # 后向填充
            df = df.fillna(method='bfill')
        elif method == 'interpolate':
            # 线性插值
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].interpolate(method='linear')
        elif method == 'drop':
            # 删除含有缺失值的行
            df = df.dropna()
        elif method == 'mean_fill':
            # 均值填充
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].mean())
        elif method == 'median_fill':
            # 中位数填充
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        elif method == 'custom':
            # 自定义填充值
            if fill_value:
                df = df.fillna(value=fill_value)
        
        logger.info(f"缺失值处理完成，方法: {method}，剩余记录数: {len(df)}")
        return df
    
    def align_time_series(self, data_dict: Dict[str, pd.DataFrame], date_column: str = 'date',
                         freq: str = 'B') -> Dict[str, pd.DataFrame]:
        """时间序列对齐"""
        if not data_dict:
            return data_dict
        
        # 找到所有数据的时间范围交集
        date_ranges = []
        for key, df in data_dict.items():
            if not df.empty and date_column in df.columns:
                df_dates = pd.to_datetime(df[date_column])
                date_ranges.append((df_dates.min(), df_dates.max()))
        
        if not date_ranges:
            return data_dict
        
        # 计算交集时间范围
        start_date = max([dr[0] for dr in date_ranges])
        end_date = min([dr[1] for dr in date_ranges])
        
        # 生成标准时间序列
        if freq == 'B':  # 工作日
            date_range = pd.bdate_range(start=start_date, end=end_date)
        else:  # 自定义频率
            date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        aligned_data = {}
        for key, df in data_dict.items():
            if not df.empty and date_column in df.columns:
                df = df.copy()
                df[date_column] = pd.to_datetime(df[date_column])
                
                # 过滤到时间范围内
                df = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
                
                # 重新索引到标准时间序列
                df = df.set_index(date_column).reindex(date_range)
                df.index.name = date_column
                df = df.reset_index()
                
                aligned_data[key] = df
            else:
                aligned_data[key] = df
        
        logger.info(f"时间序列对齐完成，时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        return aligned_data
    
    def standardize_column_names(self, df: pd.DataFrame, data_type: str = 'stock_daily') -> pd.DataFrame:
        """标准化列名"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 列名映射
        column_mapping = {
            # 股票数据标准列名映射
            '日期': 'date',
            '开盘': 'open', '开盘价': 'open',
            '最高': 'high', '最高价': 'high',
            '最低': 'low', '最低价': 'low',
            '收盘': 'close', '收盘价': 'close',
            '成交量': 'volume', '成交额': 'amount',
            '股票代码': 'symbol', '代码': 'symbol', '股票名称': 'name',
            '涨跌幅': 'change_pct', '涨跌额': 'change',
            '换手率': 'turnover_rate',
            
            # 资金流向数据标准列名映射
            '主力净流入': 'main_net_inflow',
            '主力净流入占比': 'main_net_inflow_rate',
            '超大单净流入': 'huge_net_inflow',
            '大单净流入': 'big_net_inflow',
            '中单净流入': 'medium_net_inflow',
            '小单净流入': 'small_net_inflow',
            
            # 财务数据标准列名映射
            '每股收益': 'eps', 'EPS': 'eps',
            '净资产收益率': 'roe', 'ROE': 'roe',
            '净利润': 'net_profit',
            '营业收入': 'revenue',
            '报告期': 'report_date'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        if data_type in self.standard_columns:
            for col in self.standard_columns[data_type]:
                if col not in df.columns:
                    logger.warning(f"缺少标准列: {col}")
        
        logger.info(f"列名标准化完成，数据类型: {data_type}")
        return df
    
    def standardize_stock_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化股票数据格式"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 标准化列名
        df = self.standardize_column_names(df, 'stock_daily')
        
        # 标准化日期格式
        if 'date' in df.columns:
            df = self.standardize_date_format(df, 'date')
        
        # 清洗数值列
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
        df = self.clean_numeric_data(df, numeric_columns)
        
        # 按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"股票数据标准化完成，记录数: {len(df)}")
        return df
    
    def create_time_series_features(self, df: pd.DataFrame, target_column: str = 'close', 
                                  window_sizes: List[int] = None) -> pd.DataFrame:
        """创建时间序列特征"""
        if df.empty or target_column not in df.columns:
            return df
        
        df = df.copy()
        window_sizes = window_sizes or [5, 10, 20, 30, 60]
        
        try:
            for window in window_sizes:
                # 滞后特征
                for lag in range(1, min(window + 1, 6)):  # 限制最多5个滞后特征
                    df[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
                
                # 滚动统计特征
                df[f'{target_column}_mean_{window}'] = df[target_column].rolling(window=window).mean()
                df[f'{target_column}_std_{window}'] = df[target_column].rolling(window=window).std()
                df[f'{target_column}_min_{window}'] = df[target_column].rolling(window=window).min()
                df[f'{target_column}_max_{window}'] = df[target_column].rolling(window=window).max()
                
                # 变化率特征
                df[f'{target_column}_pct_change_{window}'] = df[target_column].pct_change(periods=window)
                
                # 动量特征
                df[f'{target_column}_momentum_{window}'] = df[target_column] - df[target_column].shift(window)
            
            # 波动率特征
            df['volatility_5'] = df['close'].rolling(window=5).std() / df['close'].rolling(window=5).mean()
            df['volatility_10'] = df['close'].rolling(window=10).std() / df['close'].rolling(window=10).mean()
            
            # 价格范围特征
            if all(col in df.columns for col in ['high', 'low', 'close']):
                df['daily_range'] = (df['high'] - df['low']) / df['close']
                df['daily_range_ma5'] = df['daily_range'].rolling(window=5).mean()
            
            logger.info(f"时间序列特征创建完成，窗口大小: {window_sizes}")
            
        except Exception as e:
            logger.error(f"时间序列特征创建失败: {str(e)}")
        
        return df
    
    def normalize_data(self, df: pd.DataFrame, method: str = 'standard', 
                      exclude_columns: List[str] = None) -> Tuple[pd.DataFrame, object]:
        """数据标准化/归一化"""
        if df.empty:
            return df, None
        
        if exclude_columns is None:
            exclude_columns = ['date', 'symbol', 'index_code', 'name']
        
        df = df.copy()
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_columns = [col for col in numeric_columns if col not in exclude_columns]
        
        if not numeric_columns:
            return df, None
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        else:
            logger.error(f"不支持的标准化方法: {method}")
            return df, None
        
        try:
            df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
            logger.info(f"数据标准化完成，方法: {method}")
            return df, scaler
        except Exception as e:
            logger.error(f"数据标准化失败: {str(e)}")
            return df, None
    
    def process_stock_data(self, df: pd.DataFrame, symbol: str = None, 
                         create_features: bool = True) -> pd.DataFrame:
        """完整的股票数据处理流程"""
        if df.empty:
            return df
        
        logger.info(f"开始处理股票数据: {symbol if symbol else '未知'}")
        
        # 1. 标准化格式
        df = self.standardize_stock_data(df)
        
        # 2. 处理缺失值
        df = self.handle_missing_values(df, method=self.default_missing_method)
        
        # 3. 创建时间序列特征
        if create_features:
            df = self.create_time_series_features(df)
        
        # 4. 添加股票代码
        if symbol and 'symbol' not in df.columns:
            df['symbol'] = symbol
        
        logger.info(f"股票数据处理完成: {symbol if symbol else '未知'}，最终记录数: {len(df)}")
        return df
    
    def process_market_data(self, market_data: Dict[str, pd.DataFrame], 
                          create_features: bool = True) -> Dict[str, pd.DataFrame]:
        """处理市场数据"""
        if not market_data:
            return market_data
        
        logger.info("开始处理市场数据")
        processed_data = {}
        
        for key, df in market_data.items():
            if df.empty:
                processed_data[key] = df
                continue
            
            try:
                if 'index' in key.lower():
                    # 处理指数数据
                    df = self.standardize_column_names(df, 'index_daily')
                    df = self.standardize_date_format(df)
                    df = self.clean_numeric_data(df)
                    df = self.handle_missing_values(df)
                    if create_features:
                        df = self.create_time_series_features(df)
                elif 'money_flow' in key.lower():
                    # 处理资金流向数据
                    df = self.standardize_column_names(df, 'money_flow')
                    df = self.standardize_date_format(df)
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    df = self.clean_numeric_data(df, numeric_cols)
                    df = self.handle_missing_values(df)
                elif 'financial' in key.lower():
                    # 处理财务数据
                    df = self.standardize_column_names(df, 'financial')
                    if 'report_date' in df.columns:
                        df = self.standardize_date_format(df, 'report_date')
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    df = self.clean_numeric_data(df, numeric_cols)
                    df = self.handle_missing_values(df)
                else:
                    # 其他数据的通用处理
                    if 'date' in df.columns:
                        df = self.standardize_date_format(df)
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols:
                        df = self.clean_numeric_data(df, numeric_cols)
                    df = self.handle_missing_values(df)
                
                processed_data[key] = df
                
            except Exception as e:
                logger.error(f"处理{key}数据失败: {str(e)}")
                processed_data[key] = df
        
        # 时间对齐
        processed_data = self.align_time_series(processed_data)
        
        logger.info("市场数据处理完成")
        return processed_data
    
    def save_processed_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
                           output_path: str, file_format: str = 'csv') -> bool:
        """保存处理后的数据"""
        try:
            os.makedirs(output_path, exist_ok=True)
            
            if isinstance(data, pd.DataFrame):
                # 单个DataFrame
                file_path = os.path.join(output_path, f"processed_data.{file_format}")
                if file_format.lower() == 'csv':
                    data.to_csv(file_path, index=False)
                elif file_format.lower() == 'parquet':
                    data.to_parquet(file_path, index=False)
                elif file_format.lower() == 'json':
                    data.to_json(file_path, orient='records')
                else:
                    logger.error(f"不支持的文件格式: {file_format}")
                    return False
            else:
                # 字典形式的多个DataFrame
                for key, df in data.items():
                    if not df.empty:
                        file_path = os.path.join(output_path, f"{key}.{file_format}")
                        if file_format.lower() == 'csv':
                            df.to_csv(file_path, index=False)
                        elif file_format.lower() == 'parquet':
                            df.to_parquet(file_path, index=False)
                        elif file_format.lower() == 'json':
                            df.to_json(file_path, orient='records')
                        else:
                            logger.error(f"不支持的文件格式: {file_format}")
                            continue
            
            logger.info(f"处理后的数据已保存到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存处理后的数据失败: {str(e)}")
            return False

# 工厂函数
def get_data_preprocessor(config: Dict = None) -> StockDataPreprocessor:
    """获取数据预处理器实例"""
    return StockDataPreprocessor(config)

# 便捷函数
def preprocess_stock_data(df: pd.DataFrame, symbol: str = None, create_features: bool = True) -> pd.DataFrame:
    """预处理单只股票数据"""
    preprocessor = get_data_preprocessor()
    return preprocessor.process_stock_data(df, symbol, create_features)

def preprocess_market_data(market_data: Dict[str, pd.DataFrame], create_features: bool = True) -> Dict[str, pd.DataFrame]:
    """预处理市场数据"""
    preprocessor = get_data_preprocessor()
    return preprocessor.process_market_data(market_data, create_features)

def standardize_date_format(df: pd.DataFrame, date_column: str = 'date') -> pd.DataFrame:
    """标准化日期格式"""
    preprocessor = get_data_preprocessor()
    return preprocessor.standardize_date_format(df, date_column)

def handle_missing_values(df: pd.DataFrame, method: str = 'forward_fill') -> pd.DataFrame:
    """处理缺失值"""
    preprocessor = get_data_preprocessor()
    return preprocessor.handle_missing_values(df, method)

def create_time_series_features(df: pd.DataFrame, target_column: str = 'close', 
                               window_sizes: List[int] = None) -> pd.DataFrame:
    """创建时间序列特征"""
    preprocessor = get_data_preprocessor()
    return preprocessor.create_time_series_features(df, target_column, window_sizes)

# 为了兼容性，提供别名
DataPreprocessor = StockDataPreprocessor

# 模块结束