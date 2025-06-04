#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据服务模块
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
from fastapi import Depends

from ..core.config import settings
from ..core.logging import get_logger
from ..models.stock import (
    StockData, StockInfo, TechnicalIndicator, MarketOverview,
    DataSource, DataRequest, DataResponse
)
from ..data.csv_reader import csv_reader
from ..data.tushare_client import tushare_client

logger = get_logger(__name__)


class DataService:
    """数据服务类"""
    
    def __init__(self):
        """初始化数据服务"""
        self.data_dir = settings.DATA_DIR
        self.cache = {}
        self.cache_expire_minutes = settings.CACHE_EXPIRE_MINUTES
        self.tushare_token = settings.TUSHARE_TOKEN
        self.akshare_enabled = settings.AKSHARE_ENABLED
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"数据服务初始化完成，数据目录: {self.data_dir}")
    
    async def get_stock_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        source: DataSource = DataSource.TUSHARE,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """获取股票历史行情数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            period: 数据周期 (daily, minute)
            source: 数据源
            use_cache: 是否使用缓存
            
        Returns:
            DataFrame: 股票数据
        """
        try:
            logger.info(f"获取股票数据: {code}, 周期: {period}, 来源: {source}")
            
            # 检查缓存
            cache_key = f"{code}_{period}_{start_date}_{end_date}_{source}"
            if use_cache and cache_key in self.cache:
                cache_data = self.cache[cache_key]
                if self._is_cache_valid(cache_data['timestamp']):
                    logger.info(f"使用缓存数据: {code}")
                    return cache_data['data']
            
            # 根据数据源获取数据
            data = None
            
            if source == DataSource.TUSHARE:
                data = await self._get_tushare_data(code, start_date, end_date, period)
            elif source == DataSource.CSV:
                data = await self._get_csv_data(code, start_date, end_date, period)
            elif source == DataSource.AKSHARE:
                data = await self._get_akshare_data(code, start_date, end_date, period)
            else:
                logger.error(f"不支持的数据源: {source}")
                return None
            
            # 缓存数据
            if data is not None and use_cache:
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': datetime.now()
                }
            
            return data
            
        except Exception as e:
            logger.error(f"获取股票数据失败: {str(e)}")
            raise
    
    async def _get_tushare_data(self, code: str, start_date: Optional[str], 
                               end_date: Optional[str], period: str) -> Optional[pd.DataFrame]:
        """从Tushare获取数据"""
        try:
            logger.info(f"从Tushare获取数据: {code}")
            
            # 转换股票代码格式
            ts_code = tushare_client.convert_code_format(code, to_tushare=True)
            
            if period == "daily":
                data = tushare_client.get_daily_data(ts_code, start_date, end_date)
            elif period == "minute":
                data = tushare_client.get_minute_data(ts_code, start_date, end_date)
            else:
                logger.error(f"不支持的周期类型: {period}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"从Tushare获取数据失败: {code}, 错误: {str(e)}")
            return None
    
    async def _get_csv_data(self, code: str, start_date: Optional[str],
                           end_date: Optional[str], period: str) -> Optional[pd.DataFrame]:
        """从CSV文件获取数据"""
        try:
            logger.info(f"从CSV获取数据: {code}")
            
            if period == "daily":
                data = csv_reader.read_daily_data(code, start_date, end_date)
            elif period == "minute":
                data = csv_reader.read_minute_data(code, start_date, end_date)
            else:
                logger.error(f"不支持的周期类型: {period}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"从CSV获取数据失败: {code}, 错误: {str(e)}")
            return None
    
    async def _get_akshare_data(self, code: str, start_date: Optional[str],
                               end_date: Optional[str], period: str) -> Optional[pd.DataFrame]:
        """从AKShare获取数据"""
        try:
            logger.info(f"从AKShare获取数据: {code}")
            
            # TODO: 实现AKShare数据获取
            # 这里可以添加AKShare的具体实现
            logger.warning("AKShare数据源暂未实现")
            return None
            
        except Exception as e:
            logger.error(f"从AKShare获取数据失败: {code}, 错误: {str(e)}")
            return None
            
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """检查缓存是否有效"""
        return (datetime.now() - timestamp).total_seconds() < self.cache_expire_minutes * 60
    
    async def get_stock_basic_info(self, code: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取股票基本信息"""
        try:
            logger.info(f"获取股票基本信息: {code or '全部'}")
            
            # 优先使用Tushare
            if tushare_client.is_available():
                ts_code = tushare_client.convert_code_format(code, to_tushare=True) if code else None
                return tushare_client.get_basic_info(ts_code)
            
            logger.warning("Tushare不可用，无法获取股票基本信息")
            return None
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {str(e)}")
            return None
    
    async def get_money_flow_data(self, code: str, start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取资金流向数据"""
        try:
            logger.info(f"获取资金流向数据: {code}")
            
            if tushare_client.is_available():
                ts_code = tushare_client.convert_code_format(code, to_tushare=True)
                return tushare_client.get_money_flow(ts_code, start_date, end_date)
            
            logger.warning("Tushare不可用，无法获取资金流向数据")
            return None
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败: {str(e)}")
            return None
    
    async def get_daily_basic_data(self, code: str, trade_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取每日基本面数据"""
        try:
            logger.info(f"获取每日基本面数据: {code}")
            
            if tushare_client.is_available():
                ts_code = tushare_client.convert_code_format(code, to_tushare=True)
                return tushare_client.get_daily_basic(ts_code, trade_date)
            
            logger.warning("Tushare不可用，无法获取每日基本面数据")
            return None
            
        except Exception as e:
            logger.error(f"获取每日基本面数据失败: {str(e)}")
            return None
    
    async def list_available_stocks(self, source: DataSource = DataSource.CSV) -> List[str]:
        """列出可用的股票代码"""
        try:
            if source == DataSource.CSV:
                return csv_reader.list_available_stocks()
            elif source == DataSource.TUSHARE and tushare_client.is_available():
                basic_info = tushare_client.get_basic_info()
                if basic_info is not None:
                    return basic_info['ts_code'].tolist()
            
            return []
            
        except Exception as e:
            logger.error(f"列出可用股票失败: {str(e)}")
            return []
    
    async def get_stock_info(self, code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            logger.info(f"获取股票信息: {code}")
            
            # TODO: 实现实际的股票信息获取逻辑
            # 模拟数据
            info = {
                "code": code,
                "name": f"测试股票{code}",
                "market": "SH" if code.startswith("6") else "SZ",
                "stock_type": "stock",
                "industry": "科技",
                "sector": "电子",
                "list_date": "2010-01-01",
                "market_cap": 1000000.0,
                "float_cap": 800000.0,
                "pe_ratio": 15.5,
                "pb_ratio": 2.3,
                "is_active": True
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取股票信息失败: {str(e)}")
            raise
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览数据"""
        try:
            logger.info("获取市场概览数据")
            
            # TODO: 实现实际的市场概览数据获取逻辑
            # 模拟数据
            today = datetime.now().strftime("%Y-%m-%d")
            overview = {
                "trade_date": today,
                "total_stocks": 4000,
                "up_stocks": 2000,
                "down_stocks": 1800,
                "flat_stocks": 200,
                "limit_up_stocks": 50,
                "limit_down_stocks": 30,
                "total_volume": 5000000000,
                "total_amount": 50000000000,
                "avg_pct_change": 0.5,
                "indices": {
                    "000001": {"name": "上证指数", "close": 3000.0, "change": 15.0, "pct_change": 0.5},
                    "399001": {"name": "深证成指", "close": 10000.0, "change": 50.0, "pct_change": 0.5},
                    "399006": {"name": "创业板指", "close": 2000.0, "change": 10.0, "pct_change": 0.5}
                },
                "sector_performance": {
                    "科技": 1.2,
                    "金融": 0.5,
                    "医药": 0.8,
                    "消费": -0.3,
                    "能源": -0.5
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {str(e)}")
            raise
    
    async def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            logger.info(f"搜索股票: {keyword}")
            
            # TODO: 实现实际的股票搜索逻辑
            # 模拟数据
            results = [
                {"code": "600000", "name": "浦发银行", "market": "SH"},
                {"code": "600001", "name": "邯郸钢铁", "market": "SH"},
                {"code": "600002", "name": "齐鲁石化", "market": "SH"},
                {"code": "600003", "name": "ST东北高", "market": "SH"},
                {"code": "600004", "name": "白云机场", "market": "SH"}
            ]
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索股票失败: {str(e)}")
            raise
    
    async def get_technical_indicators(self, code: str, indicators: List[str], period: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """获取技术指标数据"""
        try:
            logger.info(f"获取技术指标: {code}, 指标: {indicators}")
            
            # 获取股票数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=period)).strftime("%Y-%m-%d")
            stock_data = await self.get_stock_data(code, start_date, end_date)
            
            if stock_data.empty:
                return {}
            
            # 计算技术指标
            result = {}
            
            # 转换为列表格式
            dates = stock_data['trade_date'].dt.strftime("%Y-%m-%d").tolist()
            prices = stock_data['close_price'].tolist()
            
            # 计算MA
            if 'ma5' in indicators or 'ma' in indicators:
                ma5 = self._calculate_ma(prices, 5)
                result['ma5'] = [{'date': d, 'value': v} for d, v in zip(dates, ma5)]
            
            if 'ma10' in indicators or 'ma' in indicators:
                ma10 = self._calculate_ma(prices, 10)
                result['ma10'] = [{'date': d, 'value': v} for d, v in zip(dates, ma10)]
            
            if 'ma20' in indicators or 'ma' in indicators:
                ma20 = self._calculate_ma(prices, 20)
                result['ma20'] = [{'date': d, 'value': v} for d, v in zip(dates, ma20)]
            
            # 计算RSI
            if 'rsi' in indicators:
                rsi = self._calculate_rsi(prices, 14)
                result['rsi'] = [{'date': d, 'value': v} for d, v in zip(dates, rsi)]
            
            # 计算MACD
            if 'macd' in indicators:
                macd, signal, hist = self._calculate_macd(prices)
                result['macd'] = [{'date': d, 'value': v} for d, v in zip(dates, macd)]
                result['macd_signal'] = [{'date': d, 'value': v} for d, v in zip(dates, signal)]
                result['macd_hist'] = [{'date': d, 'value': v} for d, v in zip(dates, hist)]
            
            return result
            
        except Exception as e:
            logger.error(f"获取技术指标失败: {str(e)}")
            raise
    
    def _calculate_ma(self, prices: List[float], window: int) -> List[float]:
        """计算移动平均线"""
        ma = []
        for i in range(len(prices)):
            if i < window - 1:
                ma.append(None)
            else:
                ma.append(sum(prices[i-window+1:i+1]) / window)
        return ma
    
    def _calculate_rsi(self, prices: List[float], window: int = 14) -> List[float]:
        """计算RSI指标"""
        deltas = np.diff(prices)
        seed = deltas[:window+1]
        up = seed[seed >= 0].sum() / window
        down = -seed[seed < 0].sum() / window
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[0] = 100. - 100. / (1. + rs)
        
        for i in range(1, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (window - 1) + upval) / window
            down = (down * (window - 1) + downval) / window
            
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi.tolist()
    
    def _calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """计算MACD指标"""
        # 计算EMA
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        # 计算MACD线
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        
        # 计算信号线
        signal_line = self._calculate_ema(macd_line, signal)
        
        # 计算柱状图
        histogram = [m - s for m, s in zip(macd_line, signal_line)]
        
        return macd_line, signal_line, histogram
    
    def _calculate_ema(self, prices: List[float], window: int) -> List[float]:
        """计算指数移动平均线"""
        ema = []
        multiplier = 2 / (window + 1)
        
        # 初始EMA值为前window个价格的简单平均值
        if len(prices) >= window:
            ema.append(sum(prices[:window]) / window)
        else:
            ema.append(prices[0] if prices else 0)
        
        # 计算剩余的EMA值
        for i in range(1, len(prices)):
            ema.append((prices[i] - ema[i-1]) * multiplier + ema[i-1])
        
        return ema
    
    async def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        try:
            status = {
                "cache_count": len(self.cache),
                "cache_keys": list(self.cache.keys()),
                "cache_expire_minutes": self.cache_expire_minutes,
                "cache_size_mb": sum(sys.getsizeof(v[0]) for v in self.cache.values()) / (1024 * 1024) if self.cache else 0
            }
            return status
            
        except Exception as e:
            logger.error(f"获取缓存状态失败: {str(e)}")
            raise
    
    async def clear_cache(self) -> bool:
        """清除缓存"""
        try:
            self.cache.clear()
            logger.info("缓存已清除")
            return True
            
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            raise