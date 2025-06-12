#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块
功能：获取每日所需数据，包括行情、资金流、新闻等
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import requests
import yaml
import os
from typing import Dict, List, Optional
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 从实例获取配置
            actual_max_retries = getattr(self, 'retry_times', max_retries)
            actual_delay = getattr(self, 'retry_delay', delay)
            
            for attempt in range(actual_max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if attempt == actual_max_retries - 1:
                        logger.error(f"{func.__name__} 重试{actual_max_retries}次后仍然失败: {e}")
                        raise e
                    else:
                        logger.warning(f"{func.__name__} 第{attempt + 1}次尝试失败: {e}, {actual_delay}秒后重试...")
                        time.sleep(actual_delay)
            return None
        return wrapper
    return decorator

class DataFetcher:
    """数据获取类 - 负责获取股票数据，支持多种股票池配置"""
    
    def __init__(self, config_path: str = "config.yaml", 
                 stock_universe: str = "default",
                 time_period: str = "medium_term"):
        """初始化数据获取器
        
        Args:
            config_path: 配置文件路径
            stock_universe: 股票池类型 (default/conservative/aggressive)
            time_period: 时间周期 (short_term/medium_term/long_term)
        """
        self.config = self._load_config(config_path)
        self.data_source_config = self.config.get('data_source', {})
        
        # 选择股票池配置
        stock_universe_configs = self.config.get('stock_universe', {})
        self.stock_universe_config = stock_universe_configs.get(stock_universe, 
                                                               stock_universe_configs.get('default', {}))
        
        # 选择时间周期配置
        time_period_configs = self.config.get('time_periods', {})
        self.time_period_config = time_period_configs.get(time_period,
                                                          time_period_configs.get('medium_term', {}))
        
        # 数据源配置
        self.retry_times = self.data_source_config.get('retry_times', 3)
        self.retry_delay = self.data_source_config.get('retry_delay', 2)
        self.timeout = self.data_source_config.get('timeout', 30)
        self.cache_enabled = self.data_source_config.get('cache_enabled', True)
        self.cache_expire_minutes = self.data_source_config.get('cache_expire_minutes', 30)
        
        # 股票池配置
        self.max_stocks = self.stock_universe_config.get('max_stocks_to_analyze', 500)
        self.min_price = self.stock_universe_config.get('min_price', 3.0)
        self.max_price = self.stock_universe_config.get('max_price', 200.0)
        self.min_market_cap = self.stock_universe_config.get('min_market_cap', 50)
        self.max_pe_ratio = self.stock_universe_config.get('max_pe_ratio', 100)
        self.exclude_st = self.stock_universe_config.get('exclude_st', True)
        self.exclude_new_stocks = self.stock_universe_config.get('exclude_new_stocks', True)
        self.exclude_boards = self.stock_universe_config.get('exclude_boards', [])
        
        # 时间配置
        self.history_days = self.time_period_config.get('history_days', 60)
        
        self.today = datetime.now().strftime('%Y%m%d')
        
        # 内存缓存
        self._cache = {} if self.cache_enabled else None
        self._cache_timestamps = {} if self.cache_enabled else None
        
        # 文件缓存配置
        self.cache_dir = Path(self.data_source_config.get('cache_dir', 'data_cache'))
        self.file_cache_enabled = self.data_source_config.get('file_cache_enabled', True)
        self.cache_expire_days = self.data_source_config.get('cache_expire_days', 7)
        
        # 创建缓存目录
        if self.file_cache_enabled:
            self._init_cache_directory()
        
        logger.info(f"数据获取器初始化完成 - 股票池: {stock_universe}, 时间周期: {time_period}")
        logger.info(f"文件缓存: {'启用' if self.file_cache_enabled else '禁用'}, 缓存目录: {self.cache_dir}")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _init_cache_directory(self):
        """初始化缓存目录结构"""
        try:
            # 创建主缓存目录
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建子目录
            (self.cache_dir / 'history').mkdir(exist_ok=True)  # 历史数据
            (self.cache_dir / 'realtime').mkdir(exist_ok=True)  # 实时数据
            (self.cache_dir / 'capital_flow').mkdir(exist_ok=True)  # 资金流向
            (self.cache_dir / 'market_data').mkdir(exist_ok=True)  # 市场数据
            
            logger.info(f"缓存目录初始化完成: {self.cache_dir}")
        except Exception as e:
            logger.error(f"初始化缓存目录失败: {e}")
            self.file_cache_enabled = False
    
    def _get_cache_file_path(self, data_type: str, stock_code: str = None, date: str = None) -> Path:
        """生成缓存文件路径
        
        Args:
            data_type: 数据类型 (history/realtime/capital_flow/market_data)
            stock_code: 股票代码
            date: 日期 (YYYYMMDD格式)
            
        Returns:
            缓存文件路径
        """
        if data_type == 'history':
            filename = f"{stock_code}_{date}_hist.csv"
            return self.cache_dir / 'history' / filename
        elif data_type == 'realtime':
            filename = f"realtime_{date}.csv"
            return self.cache_dir / 'realtime' / filename
        elif data_type == 'capital_flow':
            filename = f"capital_flow_{date}.csv"
            return self.cache_dir / 'capital_flow' / filename
        elif data_type == 'market_data':
            filename = f"market_{date}.csv"
            return self.cache_dir / 'market_data' / filename
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
    
    def _is_file_cache_valid(self, file_path: Path) -> bool:
        """检查文件缓存是否有效
        
        Args:
            file_path: 缓存文件路径
            
        Returns:
            缓存是否有效
        """
        if not self.file_cache_enabled or not file_path.exists():
            return False
        
        # 检查文件修改时间
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        current_time = datetime.now()
        time_diff = (current_time - file_mtime).days
        
        return time_diff < self.cache_expire_days
    
    def _load_from_file_cache(self, file_path: Path) -> Optional[pd.DataFrame]:
        """从文件缓存加载数据
        
        Args:
            file_path: 缓存文件路径
            
        Returns:
            缓存的数据或None
        """
        try:
            if self._is_file_cache_valid(file_path):
                data = pd.read_csv(file_path, index_col=0)
                logger.debug(f"从缓存加载数据: {file_path}")
                return data
        except Exception as e:
            logger.warning(f"读取缓存文件失败: {file_path}, 错误: {e}")
        return None
    
    def _save_to_file_cache(self, data: pd.DataFrame, file_path: Path):
        """保存数据到文件缓存
        
        Args:
            data: 要保存的数据
            file_path: 缓存文件路径
        """
        try:
            if self.file_cache_enabled and data is not None and not data.empty:
                # 确保目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                data.to_csv(file_path)
                logger.debug(f"数据已保存到缓存: {file_path}")
        except Exception as e:
            logger.warning(f"保存缓存文件失败: {file_path}, 错误: {e}")
    
    def _clean_expired_cache(self):
        """清理过期的缓存文件"""
        if not self.file_cache_enabled:
            return
        
        try:
            current_time = datetime.now()
            cleaned_count = 0
            
            for cache_subdir in ['history', 'realtime', 'capital_flow', 'market_data']:
                cache_path = self.cache_dir / cache_subdir
                if cache_path.exists():
                    for file_path in cache_path.glob('*.csv'):
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if (current_time - file_mtime).days >= self.cache_expire_days:
                            file_path.unlink()
                            cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"清理了{cleaned_count}个过期缓存文件")
        except Exception as e:
            logger.warning(f"清理缓存文件失败: {e}")
        
    @retry_on_failure()
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            # 使用akshare获取完整的A股股票列表
            stock_list = ak.stock_info_a_code_name()
            if not stock_list.empty:
                logger.info(f"获取到{len(stock_list)}只A股股票")
                return stock_list
            else:
                raise Exception("获取到的股票列表为空")
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise e
    
    def get_stock_realtime_data(self, stock_codes: List[str], force_refresh: bool = False) -> Dict[str, Dict]:
        """获取股票实时行情数据
        
        Args:
            stock_codes: 股票代码列表
            force_refresh: 是否强制刷新数据（跳过缓存）
            
        Returns:
            实时数据字典
        """
        today = datetime.now().strftime('%Y%m%d')
        
        # 检查文件缓存（实时数据缓存时间较短，仅当天有效）
        if self.file_cache_enabled and not force_refresh:
            cache_file = self._get_cache_file_path('realtime', date=today)
            cached_data = self._load_from_file_cache(cache_file)
            if cached_data is not None:
                # 从缓存数据中提取所需股票的数据
                realtime_data = {}
                for code in stock_codes:
                    stock_data = cached_data[cached_data['代码'] == code]
                    if not stock_data.empty:
                        realtime_data[code] = {
                            'name': stock_data['名称'].iloc[0],
                            'price': float(stock_data['最新价'].iloc[0]),
                            'change_pct': float(stock_data['涨跌幅'].iloc[0]),
                            'volume': int(stock_data['成交量'].iloc[0]) if pd.notna(stock_data['成交量'].iloc[0]) else 0,
                            'turnover': float(stock_data['成交额'].iloc[0]) if pd.notna(stock_data['成交额'].iloc[0]) else 0,
                            'amplitude': float(stock_data['振幅'].iloc[0]),
                            'high': float(stock_data['最高'].iloc[0]),
                            'low': float(stock_data['最低'].iloc[0]),
                            'open': float(stock_data['今开'].iloc[0]),
                            'pre_close': float(stock_data['昨收'].iloc[0])
                        }
                logger.info(f"从缓存获取{len(realtime_data)}只股票的实时数据")
                return realtime_data
        
        # 从API获取数据
        realtime_data = {}
        logger.info("从API批量获取实时行情数据...")
        all_stock_data = self._get_all_stocks_data()
        
        if all_stock_data is not None and not all_stock_data.empty:
            # 保存到文件缓存
            if self.file_cache_enabled:
                cache_file = self._get_cache_file_path('realtime', date=today)
                self._save_to_file_cache(all_stock_data, cache_file)
            
            for code in stock_codes:
                try:
                    stock_data = all_stock_data[all_stock_data['代码'] == code]
                    
                    if not stock_data.empty:
                        realtime_data[code] = {
                            'name': stock_data['名称'].iloc[0],
                            'price': float(stock_data['最新价'].iloc[0]),
                            'change_pct': float(stock_data['涨跌幅'].iloc[0]),
                            'volume': int(stock_data['成交量'].iloc[0]) if pd.notna(stock_data['成交量'].iloc[0]) else 0,
                            'turnover': float(stock_data['成交额'].iloc[0]) if pd.notna(stock_data['成交额'].iloc[0]) else 0,
                            'amplitude': float(stock_data['振幅'].iloc[0]),
                            'high': float(stock_data['最高'].iloc[0]),
                            'low': float(stock_data['最低'].iloc[0]),
                            'open': float(stock_data['今开'].iloc[0]),
                            'pre_close': float(stock_data['昨收'].iloc[0])
                        }
                    else:
                        logger.warning(f"股票{code}未找到实时数据，跳过")
                        
                except Exception as e:
                    logger.error(f"处理股票{code}实时数据失败: {e}，跳过该股票")
        else:
            logger.error("批量获取实时数据失败")
            raise Exception("无法获取实时股票数据")
                
        logger.info(f"成功获取{len(realtime_data)}只股票的实时数据")
        return realtime_data
    
    @retry_on_failure()
    def _get_all_stocks_data(self) -> pd.DataFrame:
        """获取所有股票数据"""
        return ak.stock_zh_a_spot_em()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if not self.cache_enabled or cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        current_time = datetime.now()
        time_diff = (current_time - cache_time).total_seconds() / 60
        
        return time_diff < self.cache_expire_minutes
    
    def _get_from_cache(self, cache_key: str):
        """从缓存获取数据"""
        if self.cache_enabled and self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None
    
    def _set_cache(self, cache_key: str, data):
        """设置缓存"""
        if self.cache_enabled:
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()
    
    @retry_on_failure()
    def get_stock_history_data(self, stock_code: str, period: int = None, force_refresh: bool = False) -> pd.DataFrame:
        """获取股票历史数据
        
        Args:
            stock_code: 股票代码
            period: 历史数据天数，默认使用配置中的history_days
            force_refresh: 是否强制刷新数据（跳过缓存）
            
        Returns:
            历史数据DataFrame
        """
        if period is None:
            period = self.history_days
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')
            
        # 检查内存缓存
        if not force_refresh:
            cache_key = f"hist_{stock_code}_{period}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # 检查文件缓存
        if self.file_cache_enabled and not force_refresh:
            cache_file = self._get_cache_file_path('history', stock_code, end_date)
            cached_data = self._load_from_file_cache(cache_file)
            if cached_data is not None:
                # 同时更新内存缓存
                cache_key = f"hist_{stock_code}_{period}"
                self._set_cache(cache_key, cached_data)
                return cached_data
        
        # 从API获取数据
        logger.info(f"从API获取股票{stock_code}的历史数据 ({start_date} 至 {end_date})")
        hist_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                     start_date=start_date, end_date=end_date)
        
        if not hist_data.empty:
            # 更新内存缓存
            cache_key = f"hist_{stock_code}_{period}"
            self._set_cache(cache_key, hist_data)
            
            # 更新文件缓存
            if self.file_cache_enabled:
                cache_file = self._get_cache_file_path('history', stock_code, end_date)
                self._save_to_file_cache(hist_data, cache_file)
                
            return hist_data
        else:
            logger.warning(f"股票{stock_code}历史数据为空")
            raise Exception(f"无法获取股票{stock_code}的历史数据")
    

    
    def get_capital_flow_data(self, stock_codes: List[str], force_refresh: bool = False) -> Dict[str, Dict]:
        """获取资金流向数据
        
        Args:
            stock_codes: 股票代码列表
            force_refresh: 是否强制刷新数据（跳过缓存）
            
        Returns:
            资金流向数据字典
        """
        today = datetime.now().strftime('%Y%m%d')
        
        # 检查文件缓存
        if self.file_cache_enabled and not force_refresh:
            cache_file = self._get_cache_file_path('capital_flow', date=today)
            cached_data = self._load_from_file_cache(cache_file)
            if cached_data is not None:
                # 从缓存数据中提取所需股票的数据
                capital_flow_data = {}
                for code in stock_codes:
                    if code in cached_data.index:
                        row = cached_data.loc[code]
                        capital_flow_data[code] = {
                            'main_net_inflow': row.get('main_net_inflow', 0),
                            'main_net_inflow_pct': row.get('main_net_inflow_pct', 0),
                            'super_large_net_inflow': row.get('super_large_net_inflow', 0),
                            'large_net_inflow': row.get('large_net_inflow', 0),
                            'medium_net_inflow': row.get('medium_net_inflow', 0),
                            'small_net_inflow': row.get('small_net_inflow', 0)
                        }
                logger.info(f"从缓存获取{len(capital_flow_data)}只股票的资金流向数据")
                return capital_flow_data
        
        # 从API获取数据
        capital_flow_data = {}
        logger.info("从API获取资金流向数据...")
        
        # 用于保存到缓存的DataFrame
        cache_data_list = []
        
        for code in stock_codes:
            try:
                # 获取真实的资金流向数据
                market = "sh" if code.startswith('6') else "sz"
                flow_data = ak.stock_individual_fund_flow(stock=code, market=market)
                
                if flow_data is not None and not flow_data.empty:
                    latest_data = flow_data.iloc[-1]
                    flow_info = {
                        'main_net_inflow': latest_data.get('主力净流入-净额', 0),
                        'main_net_inflow_pct': latest_data.get('主力净流入-净占比', 0),
                        'super_large_net_inflow': latest_data.get('超大单净流入-净额', 0),
                        'large_net_inflow': latest_data.get('大单净流入-净额', 0),
                        'medium_net_inflow': latest_data.get('中单净流入-净额', 0),
                        'small_net_inflow': latest_data.get('小单净流入-净额', 0)
                    }
                    capital_flow_data[code] = flow_info
                    
                    # 添加到缓存数据列表
                    cache_row = flow_info.copy()
                    cache_row['stock_code'] = code
                    cache_data_list.append(cache_row)
                else:
                    logger.warning(f"股票{code}资金流向数据为空，跳过")
                
            except Exception as e:
                logger.warning(f"获取股票{code}资金流向数据失败: {e}，跳过该股票")
        
        # 保存到文件缓存
        if self.file_cache_enabled and cache_data_list:
            cache_df = pd.DataFrame(cache_data_list)
            cache_df.set_index('stock_code', inplace=True)
            cache_file = self._get_cache_file_path('capital_flow', date=today)
            self._save_to_file_cache(cache_df, cache_file)
                
        logger.info(f"成功获取{len(capital_flow_data)}只股票的资金流向数据")
        return capital_flow_data
    
    def filter_stock_universe(self, stock_list: pd.DataFrame) -> List[str]:
        """根据配置过滤股票池
        
        Args:
            stock_list: 原始股票列表
            
        Returns:
            过滤后的股票代码列表
        """
        if stock_list.empty:
            return []
        
        logger.info(f"开始过滤股票池，原始股票数量: {len(stock_list)}")
        
        filtered_codes = []
        
        for _, stock in stock_list.iterrows():
            stock_code = stock['code']
            stock_name = stock.get('name', '')
            
            # 排除ST股票
            if self.exclude_st and ('ST' in stock_name or '*ST' in stock_name):
                continue
            
            # 排除特定板块
            if any(stock_code.startswith(board) for board in self.exclude_boards):
                continue
            
            # 获取实时数据进行进一步过滤
            try:
                realtime_data = self.get_stock_realtime_data([stock_code])
                if stock_code not in realtime_data:
                    continue
                
                stock_data = realtime_data[stock_code]
                price = stock_data.get('price', 0)
                
                # 价格过滤
                if price < self.min_price or price > self.max_price:
                    continue
                
                # 成交额过滤（流动性）
                turnover = stock_data.get('turnover', 0)
                if turnover < 10000000:  # 成交额小于1000万
                    continue
                
                filtered_codes.append(stock_code)
                
                # 限制数量
                if len(filtered_codes) >= self.max_stocks:
                    break
                    
            except Exception as e:
                logger.warning(f"过滤股票{stock_code}时出错: {e}，跳过")
                continue
        
        logger.info(f"股票池过滤完成，剩余股票数量: {len(filtered_codes)}")
        return filtered_codes
    
    def get_all_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取所有股票的完整数据
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            包含所有数据的字典
        """
        logger.info(f"开始获取{len(stock_codes)}只股票的完整数据")
        
        all_data = {}
        
        # 批量获取实时数据
        realtime_data = self.get_stock_realtime_data(stock_codes)
        
        # 批量获取资金流向数据
        capital_flow_data = self.get_capital_flow_data(stock_codes)
        
        for stock_code in stock_codes:
            try:
                # 获取历史数据
                hist_data = self.get_stock_history_data(stock_code)
                
                all_data[stock_code] = {
                    'realtime_data': realtime_data.get(stock_code, {}),
                    'history_data': hist_data,
                    'capital_flow_data': capital_flow_data.get(stock_code, {})
                }
                
            except Exception as e:
                logger.error(f"获取股票{stock_code}数据失败: {e}，跳过该股票")
                continue
        
        logger.info(f"成功获取{len(all_data)}只股票的完整数据")
        return all_data
    
    def get_market_sentiment_data(self) -> Dict[str, float]:
        """获取市场情绪数据"""
        sentiment_data = {}
        
        # 获取涨跌停数据
        try:
            limit_data = ak.stock_zt_pool_em(date=self.today)
            sentiment_data['limit_up_count'] = len(limit_data) if not limit_data.empty else 0
        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            raise e
        
        # 获取市场总体涨跌情况
        try:
            market_data = ak.stock_zh_a_spot_em()
            if not market_data.empty:
                up_count = len(market_data[market_data['涨跌幅'] > 0])
                down_count = len(market_data[market_data['涨跌幅'] < 0])
                total_count = len(market_data)
                
                sentiment_data['up_ratio'] = up_count / total_count if total_count > 0 else 0
                sentiment_data['down_ratio'] = down_count / total_count if total_count > 0 else 0
            else:
                raise Exception("市场数据为空")
        except Exception as e:
            logger.error(f"获取市场涨跌数据失败: {e}")
            raise e
        
        logger.info(f"市场情绪数据: 涨停{sentiment_data['limit_up_count']}只, 上涨比例{sentiment_data['up_ratio']:.2%}")
        return sentiment_data
    
    def get_news_sentiment(self, stock_codes: List[str]) -> Dict[str, float]:
        """获取新闻情绪数据（简化版）"""
        # 这里可以接入新闻API或爬虫获取新闻情绪
        # 暂时返回随机情绪分数作为示例
        news_sentiment = {}
        
        for code in stock_codes:
            # 实际应用中这里应该是真实的新闻情绪分析
            news_sentiment[code] = np.random.uniform(0.3, 0.7)  # 0-1之间的情绪分数
            
        return news_sentiment
    
    def get_all_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取所有需要的数据"""
        logger.info("开始获取所有数据...")
        
        all_data = {}
        
        # 获取实时行情数据
        logger.info("获取实时行情数据...")
        realtime_data = self.get_stock_realtime_data(stock_codes)
        
        # 获取资金流向数据
        logger.info("获取资金流向数据...")
        capital_flow_data = self.get_capital_flow_data(stock_codes)
        
        # 获取市场情绪数据
        logger.info("获取市场情绪数据...")
        market_sentiment = self.get_market_sentiment_data()
        
        # 获取新闻情绪数据
        logger.info("获取新闻情绪数据...")
        news_sentiment = self.get_news_sentiment(stock_codes)
        
        # 只处理有实时数据的股票
        for code in realtime_data.keys():
            all_data[code] = {
                'realtime': realtime_data.get(code, {}),
                'capital_flow': capital_flow_data.get(code, {}),
                'market_sentiment': market_sentiment,
                'news_sentiment': news_sentiment.get(code, 0.5)
            }
        
        logger.info(f"成功获取{len(all_data)}只股票的完整数据")
        return all_data
    
    def filter_stock_universe(self, stock_list: pd.DataFrame) -> List[str]:
        """筛选股票池
        
        Args:
            stock_list: 股票列表DataFrame
            
        Returns:
            筛选后的股票代码列表
        """
        logger.info("开始筛选股票池...")
        
        if stock_list.empty:
            logger.warning("股票列表为空")
            return []
        
        filtered_codes = []
        
        for _, stock in stock_list.iterrows():
            stock_code = stock.get('code', '')
            stock_name = stock.get('name', '')
            
            # 基本过滤条件
            if not stock_code or not stock_name:
                continue
            
            # 排除ST股票
            if self.exclude_st and ('ST' in stock_name or '*ST' in stock_name):
                continue
            
            # 排除指定板块
            should_exclude = False
            for board in self.exclude_boards:
                if stock_code.startswith(board):
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            filtered_codes.append(stock_code)
        
        # 限制分析数量
        if len(filtered_codes) > self.max_stocks:
            filtered_codes = filtered_codes[:self.max_stocks]
        
        logger.info(f"筛选后股票池包含{len(filtered_codes)}只股票")
        return filtered_codes
    
    def validate_stock_data(self, stock_data: Dict) -> bool:
        """验证股票数据的有效性
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            数据是否有效
        """
        realtime = stock_data.get('realtime', {})
        
        # 检查价格范围
        price = realtime.get('price', 0)
        if price < self.min_price or price > self.max_price:
            return False
        
        # 检查基本数据完整性
        required_fields = ['price', 'volume', 'turnover']
        for field in required_fields:
            if field not in realtime or realtime[field] is None:
                return False
        
        return True