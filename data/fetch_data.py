#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据获取模块
负责从本地或API拉取A股行情、资金、情绪等原始数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
import time
import os
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockDataFetcher:
    """A股数据获取器"""
    
    def __init__(self, data_source: str = 'akshare', local_data_path: str = None, akshare_config: dict = None):
        """
        初始化数据获取器
        
        Args:
            data_source: 数据源类型，'akshare'或'local'
            local_data_path: 本地数据路径，当data_source为'local'时必须提供
            akshare_config: AKShare配置参数
        """
        self.data_source = data_source
        self.local_data_path = local_data_path
        
        # AKShare配置
        self.akshare_config = akshare_config or {}
        self.adjust = self.akshare_config.get('adjust', 'qfq')
        self.period = self.akshare_config.get('period', 'daily')
        self.request_delay = self.akshare_config.get('request_delay', 0.2)
        self.retry_times = self.akshare_config.get('retry_times', 3)
        self.retry_delay = self.akshare_config.get('retry_delay', 1)
        
        # 如果使用本地数据，检查路径是否存在
        if data_source == 'local' and (local_data_path is None or not os.path.exists(local_data_path)):
            logger.warning(f"本地数据路径不存在: {local_data_path}，将切换到AKShare模式")
            self.data_source = 'akshare'
    
    def _retry_request(self, func, *args, **kwargs):
        """重试机制"""
        for i in range(self.retry_times):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"请求失败，第{i+1}次重试: {str(e)}")
                if i < self.retry_times - 1:
                    time.sleep(self.retry_delay * (i + 1))  # 指数退避
                else:
                    logger.error(f"请求最终失败: {str(e)}")
                    raise e
    
    def _read_local_data(self, file_path: str) -> pd.DataFrame:
        """读取本地数据"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"本地数据文件不存在: {file_path}")
                return pd.DataFrame()
            
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                return pd.read_csv(file_path)
            elif file_ext == '.parquet':
                return pd.read_parquet(file_path)
            elif file_ext == '.json':
                return pd.read_json(file_path)
            elif file_ext == '.pkl':
                return pd.read_pickle(file_path)
            else:
                logger.error(f"不支持的文件格式: {file_ext}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"读取本地数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'stock_list.csv')
            return self._read_local_data(file_path)
        else:
            try:
                logger.info("获取A股股票列表...")
                stock_list = self._retry_request(ak.stock_info_a_code_name)
                return stock_list
            except Exception as e:
                logger.error(f"获取股票列表失败: {str(e)}")
                return pd.DataFrame()
    
    def get_stock_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取个股日线数据"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'daily', f"{symbol}.csv")
            data = self._read_local_data(file_path)
            if not data.empty and 'date' in data.columns:
                # 过滤日期范围
                data['date'] = pd.to_datetime(data['date'])
                mask = (data['date'] >= pd.to_datetime(start_date)) & (data['date'] <= pd.to_datetime(end_date))
                data = data[mask].copy()
                if not data.empty:
                    data['symbol'] = symbol
            return data
        else:
            try:
                logger.info(f"获取{symbol}日线数据: {start_date} - {end_date}")
                data = self._retry_request(
                    ak.stock_zh_a_hist,
                    symbol=symbol,
                    period=self.period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=self.adjust
                )
                if not data.empty:
                    data['symbol'] = symbol
                return data
            except Exception as e:
                logger.error(f"获取{symbol}日线数据失败: {str(e)}")
                return pd.DataFrame()
    
    def get_market_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取市场指数数据"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'index', f"{index_code}.csv")
            data = self._read_local_data(file_path)
            if not data.empty and 'date' in data.columns:
                # 过滤日期范围
                data['date'] = pd.to_datetime(data['date'])
                mask = (data['date'] >= pd.to_datetime(start_date)) & (data['date'] <= pd.to_datetime(end_date))
                data = data[mask].copy()
                if not data.empty:
                    data['index_code'] = index_code
            return data
        else:
            try:
                logger.info(f"获取指数{index_code}数据")
                # AKShare的stock_zh_index_daily函数不支持日期参数，返回全部历史数据
                data = self._retry_request(
                    ak.stock_zh_index_daily,
                    symbol=index_code
                )
                if not data.empty:
                    data['index_code'] = index_code
                    # 手动过滤日期范围
                    if 'date' in data.columns:
                        data['date'] = pd.to_datetime(data['date'])
                        mask = (data['date'] >= pd.to_datetime(start_date)) & (data['date'] <= pd.to_datetime(end_date))
                        data = data[mask].copy()
                return data
            except Exception as e:
                logger.error(f"获取指数{index_code}数据失败: {str(e)}")
                return pd.DataFrame()
    
    def get_money_flow_data(self, symbol: str) -> pd.DataFrame:
        """获取个股资金流向数据"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'money_flow', f"{symbol}.csv")
            data = self._read_local_data(file_path)
            if not data.empty:
                data['symbol'] = symbol
            return data
        else:
            try:
                logger.info(f"获取{symbol}资金流向数据...")
                data = self._retry_request(ak.stock_individual_fund_flow, stock=symbol)
                if not data.empty:
                    data['symbol'] = symbol
                return data
            except Exception as e:
                logger.error(f"获取{symbol}资金流向数据失败: {str(e)}")
                return pd.DataFrame()
    
    def get_market_money_flow(self) -> pd.DataFrame:
        """获取市场整体资金流向"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'market_money_flow.csv')
            return self._read_local_data(file_path)
        else:
            try:
                logger.info("获取市场整体资金流向数据...")
                data = self._retry_request(ak.stock_market_fund_flow)
                return data
            except Exception as e:
                logger.error(f"获取市场资金流向数据失败: {str(e)}")
                return pd.DataFrame()
    
    def get_sentiment_data(self) -> pd.DataFrame:
        """获取市场情绪数据"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'sentiment.csv')
            return self._read_local_data(file_path)
        else:
            try:
                logger.info("获取市场情绪数据...")
                # 获取涨跌停数据作为情绪指标
                limit_data = self._retry_request(ak.stock_zt_pool_em)
                return limit_data
            except Exception as e:
                logger.error(f"获取市场情绪数据失败: {str(e)}")
                return pd.DataFrame()
    
    def get_financial_data(self, symbol: str) -> pd.DataFrame:
        """获取财务数据"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'financial', f"{symbol}.csv")
            data = self._read_local_data(file_path)
            if not data.empty:
                data['symbol'] = symbol
            return data
        else:
            try:
                logger.info(f"获取{symbol}财务数据...")
                # 获取最近的财务指标
                data = self._retry_request(ak.stock_financial_abstract, symbol=symbol)
                if not data.empty:
                    data['symbol'] = symbol
                return data
            except Exception as e:
                logger.error(f"获取{symbol}财务数据失败: {str(e)}")
                return pd.DataFrame()
    
    def get_industry_data(self) -> pd.DataFrame:
        """获取行业数据"""
        if self.data_source == 'local':
            file_path = os.path.join(self.local_data_path, 'industry.csv')
            return self._read_local_data(file_path)
        else:
            try:
                logger.info("获取行业数据...")
                # 获取行业分类数据
                data = self._retry_request(ak.stock_sector_spot)
                return data
            except Exception as e:
                logger.error(f"获取行业数据失败: {str(e)}")
                return pd.DataFrame()
    
    def batch_fetch_stock_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """批量获取股票数据"""
        stock_data = {}
        total = len(symbols)
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"正在获取第{i}/{total}只股票: {symbol}")
            try:
                data = self.get_stock_daily_data(symbol, start_date, end_date)
                if not data.empty:
                    stock_data[symbol] = data
                # 添加延时避免请求过快
                if self.data_source == 'akshare':
                    time.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"获取{symbol}数据失败: {str(e)}")
                continue
        
        return stock_data
    
    def save_data_to_local(self, data: pd.DataFrame, file_path: str, file_format: str = 'csv') -> bool:
        """保存数据到本地"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 根据格式保存
            if file_format.lower() == 'csv':
                data.to_csv(file_path, index=False)
            elif file_format.lower() == 'parquet':
                data.to_parquet(file_path, index=False)
            elif file_format.lower() == 'json':
                data.to_json(file_path, orient='records')
            elif file_format.lower() == 'pkl':
                data.to_pickle(file_path)
            else:
                logger.error(f"不支持的文件格式: {file_format}")
                return False
            
            logger.info(f"数据已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            return False

# 工厂函数
def get_data_fetcher(data_source: str = 'akshare', local_data_path: str = None, akshare_config: dict = None) -> StockDataFetcher:
    """获取数据获取器实例"""
    return StockDataFetcher(data_source, local_data_path, akshare_config)

# 便捷函数
def fetch_stock_list() -> pd.DataFrame:
    """获取股票列表"""
    fetcher = get_data_fetcher()
    return fetcher.get_stock_list()

def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取单只股票数据"""
    fetcher = get_data_fetcher()
    return fetcher.get_stock_daily_data(symbol, start_date, end_date)

def fetch_batch_stock_data(symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """批量获取股票数据"""
    fetcher = get_data_fetcher()
    return fetcher.batch_fetch_stock_data(symbols, start_date, end_date)

def fetch_market_data(start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """获取市场数据"""
    fetcher = get_data_fetcher()
    market_data = {}
    
    # 主要指数
    indices = ['sh000001', 'sz399001', 'sz399006']  # 上证指数、深证成指、创业板指
    for index_code in indices:
        data = fetcher.get_market_index_data(index_code, start_date, end_date)
        if not data.empty:
            market_data[f'index_{index_code}'] = data
    
    # 市场资金流向
    money_flow = fetcher.get_market_money_flow()
    if not money_flow.empty:
        market_data['market_money_flow'] = money_flow
    
    # 市场情绪
    sentiment = fetcher.get_sentiment_data()
    if not sentiment.empty:
        market_data['market_sentiment'] = sentiment
    
    # 行业数据
    industry = fetcher.get_industry_data()
    if not industry.empty:
        market_data['industry'] = industry
    
    return market_data

def fetch_from_local(data_path: str, data_type: str, symbol: str = None, 
                    start_date: str = None, end_date: str = None) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """从本地获取数据"""
    fetcher = get_data_fetcher('local', data_path)
    
    if data_type == 'stock_list':
        return fetcher.get_stock_list()
    elif data_type == 'stock_daily':
        if symbol:
            return fetcher.get_stock_daily_data(symbol, start_date or '19900101', end_date or datetime.now().strftime('%Y%m%d'))
        else:
            logger.error("获取股票日线数据需要提供股票代码")
            return pd.DataFrame()
    elif data_type == 'market_index':
        indices = ['sh000001', 'sz399001', 'sz399006']
        result = {}
        for idx in indices:
            data = fetcher.get_market_index_data(idx, start_date or '19900101', end_date or datetime.now().strftime('%Y%m%d'))
            if not data.empty:
                result[idx] = data
        return result
    elif data_type == 'money_flow':
        return fetcher.get_market_money_flow()
    elif data_type == 'sentiment':
        return fetcher.get_sentiment_data()
    else:
        logger.error(f"不支持的数据类型: {data_type}")
        return pd.DataFrame()

# 模块结束