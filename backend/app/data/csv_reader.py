# -*- coding: utf-8 -*-
"""
CSV数据读取模块
支持日K、分钟K、本地测试数据的读取
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
from pathlib import Path

from ..core.config import settings
from ..core.logging import get_logger
from ..models.stock import StockData, DataSource

logger = get_logger(__name__)


class CSVDataReader:
    """CSV数据读取器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """初始化CSV数据读取器
        
        Args:
            data_dir: 数据目录路径，默认使用配置中的DATA_DIR
        """
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.csv_dir = self.data_dir / "csv"
        
        # 确保CSV数据目录存在
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CSV数据读取器初始化完成，数据目录: {self.csv_dir}")
    
    def read_daily_data(self, code: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """读取日K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            DataFrame: 包含日K线数据的DataFrame
        """
        try:
            # 构建文件路径
            file_path = self.csv_dir / "daily" / f"{code}.csv"
            
            if not file_path.exists():
                logger.warning(f"日K线数据文件不存在: {file_path}")
                return None
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            # 日期过滤
            if start_date or end_date:
                df = self._filter_by_date(df, start_date, end_date)
            
            # 数据验证和清洗
            df = self._validate_and_clean_data(df)
            
            logger.info(f"成功读取日K线数据: {code}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"读取日K线数据失败: {code}, 错误: {str(e)}")
            return None
    
    def read_minute_data(self, code: str, start_date: Optional[str] = None,
                        end_date: Optional[str] = None, 
                        minute_type: str = "1min") -> Optional[pd.DataFrame]:
        """读取分钟K线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            minute_type: 分钟类型 (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            DataFrame: 包含分钟K线数据的DataFrame
        """
        try:
            # 构建文件路径
            file_path = self.csv_dir / "minute" / minute_type / f"{code}.csv"
            
            if not file_path.exists():
                logger.warning(f"分钟K线数据文件不存在: {file_path}")
                return None
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            # 日期过滤
            if start_date or end_date:
                df = self._filter_by_date(df, start_date, end_date)
            
            # 数据验证和清洗
            df = self._validate_and_clean_data(df)
            
            logger.info(f"成功读取{minute_type}分钟K线数据: {code}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"读取分钟K线数据失败: {code}, 错误: {str(e)}")
            return None
    
    def read_test_data(self, filename: str) -> Optional[pd.DataFrame]:
        """读取本地测试数据
        
        Args:
            filename: 测试数据文件名
            
        Returns:
            DataFrame: 测试数据
        """
        try:
            file_path = self.csv_dir / "test" / filename
            
            if not file_path.exists():
                logger.warning(f"测试数据文件不存在: {file_path}")
                return None
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            # 数据验证和清洗
            df = self._validate_and_clean_data(df)
            
            logger.info(f"成功读取测试数据: {filename}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"读取测试数据失败: {filename}, 错误: {str(e)}")
            return None
    
    def list_available_stocks(self, data_type: str = "daily") -> List[str]:
        """列出可用的股票代码
        
        Args:
            data_type: 数据类型 (daily, minute)
            
        Returns:
            List[str]: 可用的股票代码列表
        """
        try:
            if data_type == "daily":
                data_dir = self.csv_dir / "daily"
            elif data_type == "minute":
                data_dir = self.csv_dir / "minute" / "1min"  # 默认使用1分钟数据
            else:
                logger.error(f"不支持的数据类型: {data_type}")
                return []
            
            if not data_dir.exists():
                return []
            
            # 获取所有CSV文件
            csv_files = list(data_dir.glob("*.csv"))
            
            # 提取股票代码
            stock_codes = [f.stem for f in csv_files]
            
            logger.info(f"找到{data_type}数据股票数量: {len(stock_codes)}")
            return sorted(stock_codes)
            
        except Exception as e:
            logger.error(f"列出可用股票失败: {str(e)}")
            return []
    
    def save_data_to_csv(self, data: pd.DataFrame, code: str, 
                        data_type: str = "daily", minute_type: str = "1min") -> bool:
        """保存数据到CSV文件
        
        Args:
            data: 要保存的数据
            code: 股票代码
            data_type: 数据类型 (daily, minute, test)
            minute_type: 分钟类型 (仅当data_type为minute时有效)
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 构建保存路径
            if data_type == "daily":
                save_dir = self.csv_dir / "daily"
                file_path = save_dir / f"{code}.csv"
            elif data_type == "minute":
                save_dir = self.csv_dir / "minute" / minute_type
                file_path = save_dir / f"{code}.csv"
            elif data_type == "test":
                save_dir = self.csv_dir / "test"
                file_path = save_dir / f"{code}.csv"
            else:
                logger.error(f"不支持的数据类型: {data_type}")
                return False
            
            # 确保目录存在
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存数据
            data.to_csv(file_path, index=False, encoding='utf-8')
            
            logger.info(f"数据保存成功: {file_path}, 数据量: {len(data)}")
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {code}, 错误: {str(e)}")
            return False
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名
        
        Args:
            df: 原始DataFrame
            
        Returns:
            DataFrame: 标准化后的DataFrame
        """
        # 定义列名映射
        column_mapping = {
            # 中文列名映射
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high', 
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_change',
            '换手率': 'turnover',
            
            # 英文列名映射
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low', 
            'Close': 'close',
            'Volume': 'volume',
            'Amount': 'amount',
            'Pct_change': 'pct_change',
            'Turnover': 'turnover',
            
            # 其他可能的列名
            'trade_date': 'date',
            'ts_code': 'code',
            'vol': 'volume',
            'pre_close': 'pre_close',
            'change': 'change'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保日期列存在且格式正确
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        return df
    
    def _filter_by_date(self, df: pd.DataFrame, start_date: Optional[str], 
                       end_date: Optional[str]) -> pd.DataFrame:
        """按日期过滤数据
        
        Args:
            df: 原始DataFrame
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 过滤后的DataFrame
        """
        if 'date' not in df.columns:
            return df
        
        # 确保日期列是datetime类型
        df['date'] = pd.to_datetime(df['date'])
        
        # 应用日期过滤
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df['date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df['date'] <= end_dt]
        
        # 转换回字符串格式
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        return df
    
    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证和清洗数据
        
        Args:
            df: 原始DataFrame
            
        Returns:
            DataFrame: 清洗后的DataFrame
        """
        if df.empty:
            return df
        
        # 删除重复行
        df = df.drop_duplicates()
        
        # 处理缺失值
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in numeric_columns:
            if col in df.columns:
                # 将非数值转换为NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # 删除关键价格数据缺失的行
                if col in ['open', 'high', 'low', 'close']:
                    df = df.dropna(subset=[col])
        
        # 按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df


# 创建全局实例
csv_reader = CSVDataReader()