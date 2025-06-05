"""数据管理器

统一管理多个数据源，提供数据获取、缓存和同步功能。
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import asyncio
from loguru import logger

from .sources.base import BaseDataSource
from .sources.tushare_source import TushareSource
from .sources.sina_source import SinaSource
from .sources.eastmoney_source import EastMoneySource
from .sources.csv_source import CSVSource
from .cache import DataCache
from config.settings import settings, DATA_SOURCES


@dataclass
class StockData:
    """股票数据结构"""
    code: str
    name: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover_rate: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None


@dataclass
class MarketData:
    """市场数据结构"""
    date: date
    index_code: str
    index_name: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    change_pct: float


class DataManager:
    """数据管理器
    
    负责协调多个数据源，提供统一的数据访问接口。
    """
    
    def __init__(self):
        self.sources: List[BaseDataSource] = []
        self.cache = DataCache()
        self._initialize_sources()
        
    def _initialize_sources(self):
        """初始化数据源"""
        # 按优先级排序的数据源
        source_configs = sorted(
            DATA_SOURCES.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        for source_name, config in source_configs:
            if not config.get('enabled', False):
                continue
                
            try:
                if source_name == 'tushare':
                    source = TushareSource(config)
                elif source_name == 'sina':
                    source = SinaSource(config)
                elif source_name == 'eastmoney':
                    source = EastMoneySource(config)
                elif source_name == 'csv':
                    source = CSVSource(config)
                else:
                    logger.warning(f"未知数据源: {source_name}")
                    continue
                    
                self.sources.append(source)
                logger.info(f"已加载数据源: {source_name}")
                
            except Exception as e:
                logger.error(f"加载数据源 {source_name} 失败: {e}")
    
    async def get_stock_list(self, market: str = 'A') -> List[Dict[str, Any]]:
        """获取股票列表
        
        Args:
            market: 市场类型 ('A', 'HK', 'US')
            
        Returns:
            股票列表
        """
        cache_key = f"stock_list_{market}"
        
        # 尝试从缓存获取
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # 从数据源获取
        for source in self.sources:
            try:
                data = await source.get_stock_list(market)
                if data:
                    # 缓存数据
                    await self.cache.set(cache_key, data, expire=3600)  # 1小时缓存
                    return data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取股票列表失败: {e}")
                continue
                
        logger.error("所有数据源获取股票列表失败")
        return []
    
    async def get_stock_data(
        self,
        code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = 'daily'
    ) -> List[StockData]:
        """获取股票历史数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期 ('daily', '5min', '15min', '30min', '60min')
            
        Returns:
            股票数据列表
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        cache_key = f"stock_data_{code}_{start_date}_{end_date}_{period}"
        
        # 尝试从缓存获取
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [StockData(**item) for item in cached_data]
            
        # 从数据源获取
        for source in self.sources:
            try:
                data = await source.get_stock_data(code, start_date, end_date, period)
                if data:
                    # 转换为StockData对象
                    stock_data = [StockData(**item) for item in data]
                    
                    # 缓存数据
                    cache_data = [item.__dict__ for item in stock_data]
                    await self.cache.set(cache_key, cache_data, expire=1800)  # 30分钟缓存
                    
                    return stock_data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取股票数据失败: {e}")
                continue
                
        logger.error(f"所有数据源获取股票 {code} 数据失败")
        return []
    
    async def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时行情数据
        
        Args:
            codes: 股票代码列表
            
        Returns:
            实时数据字典
        """
        cache_key = f"realtime_data_{'_'.join(sorted(codes))}"
        
        # 尝试从缓存获取（短期缓存）
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # 从数据源获取
        for source in self.sources:
            try:
                data = await source.get_realtime_data(codes)
                if data:
                    # 缓存数据（1分钟缓存）
                    await self.cache.set(cache_key, data, expire=60)
                    return data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取实时数据失败: {e}")
                continue
                
        logger.error("所有数据源获取实时数据失败")
        return {}
    
    async def get_market_data(
        self,
        index_code: str = '000001.SH',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketData]:
        """获取市场指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            市场数据列表
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        cache_key = f"market_data_{index_code}_{start_date}_{end_date}"
        
        # 尝试从缓存获取
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return [MarketData(**item) for item in cached_data]
            
        # 从数据源获取
        for source in self.sources:
            try:
                data = await source.get_market_data(index_code, start_date, end_date)
                if data:
                    # 转换为MarketData对象
                    market_data = [MarketData(**item) for item in data]
                    
                    # 缓存数据
                    cache_data = [item.__dict__ for item in market_data]
                    await self.cache.set(cache_key, cache_data, expire=1800)  # 30分钟缓存
                    
                    return market_data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取市场数据失败: {e}")
                continue
                
        logger.error(f"所有数据源获取市场数据失败")
        return []
    
    async def get_fundamental_data(self, code: str) -> Dict[str, Any]:
        """获取基本面数据
        
        Args:
            code: 股票代码
            
        Returns:
            基本面数据
        """
        cache_key = f"fundamental_data_{code}"
        
        # 尝试从缓存获取
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # 从数据源获取
        for source in self.sources:
            try:
                data = await source.get_fundamental_data(code)
                if data:
                    # 缓存数据（1小时缓存）
                    await self.cache.set(cache_key, data, expire=3600)
                    return data
            except Exception as e:
                logger.warning(f"数据源 {source.name} 获取基本面数据失败: {e}")
                continue
                
        logger.error(f"所有数据源获取股票 {code} 基本面数据失败")
        return {}
    
    async def sync_data(self):
        """同步数据
        
        定期同步最新数据到缓存
        """
        logger.info("开始同步数据")
        
        try:
            # 获取股票列表
            stock_list = await self.get_stock_list()
            logger.info(f"同步股票列表: {len(stock_list)} 只股票")
            
            # 获取主要指数数据
            major_indices = ['000001.SH', '399001.SZ', '399006.SZ']
            for index_code in major_indices:
                await self.get_market_data(index_code)
                
            # 获取热门股票的实时数据
            if stock_list:
                hot_stocks = [stock['code'] for stock in stock_list[:100]]  # 前100只股票
                await self.get_realtime_data(hot_stocks)
                
            logger.info("数据同步完成")
            
        except Exception as e:
            logger.error(f"数据同步失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            各数据源的健康状态
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'cache': await self.cache.health_check()
        }
        
        for source in self.sources:
            try:
                status = await source.health_check()
                health_status['sources'][source.name] = {
                    'status': 'healthy' if status else 'unhealthy',
                    'last_check': datetime.now().isoformat()
                }
            except Exception as e:
                health_status['sources'][source.name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
                
        return health_status