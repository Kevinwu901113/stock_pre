# -*- coding: utf-8 -*-
"""
Tushare接口封装模块
包括基础行情、指标、资金流向等数据获取
"""

import tushare as ts
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timedelta
import time
from functools import wraps

from ..core.config import settings
from ..core.logging import get_logger
from ..models.stock import StockData, DataSource

logger = get_logger(__name__)


def rate_limit(calls_per_minute: int = 200):
    """API调用频率限制装饰器"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


class TushareClient:
    """Tushare数据客户端"""
    
    def __init__(self, token: Optional[str] = None):
        """初始化Tushare客户端
        
        Args:
            token: Tushare API token，默认使用配置中的token
        """
        self.token = token or settings.TUSHARE_TOKEN
        
        if not self.token:
            logger.warning("Tushare token未配置，部分功能可能无法使用")
            self.pro = None
        else:
            try:
                ts.set_token(self.token)
                self.pro = ts.pro_api()
                logger.info("Tushare客户端初始化成功")
            except Exception as e:
                logger.error(f"Tushare客户端初始化失败: {str(e)}")
                self.pro = None
    
    def is_available(self) -> bool:
        """检查Tushare是否可用"""
        return self.pro is not None
    
    @rate_limit(calls_per_minute=200)
    def get_daily_data(self, ts_code: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取日K线数据
        
        Args:
            ts_code: Tushare股票代码 (如: 000001.SZ)
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            DataFrame: 日K线数据
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            # 转换日期格式
            if start_date:
                start_date = start_date.replace('-', '')
            if end_date:
                end_date = end_date.replace('-', '')
            
            # 获取数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.warning(f"未获取到日K线数据: {ts_code}")
                return None
            
            # 数据处理
            df = self._process_daily_data(df)
            
            logger.info(f"获取日K线数据成功: {ts_code}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取日K线数据失败: {ts_code}, 错误: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=200)
    def get_minute_data(self, ts_code: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None, freq: str = '1min') -> Optional[pd.DataFrame]:
        """获取分钟K线数据
        
        Args:
            ts_code: Tushare股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            freq: 频率 (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            DataFrame: 分钟K线数据
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            # 转换日期格式
            if start_date:
                start_date = start_date.replace('-', '')
            if end_date:
                end_date = end_date.replace('-', '')
            
            # 获取数据
            df = self.pro.stk_mins(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                freq=freq
            )
            
            if df.empty:
                logger.warning(f"未获取到分钟K线数据: {ts_code}")
                return None
            
            # 数据处理
            df = self._process_minute_data(df)
            
            logger.info(f"获取{freq}分钟K线数据成功: {ts_code}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取分钟K线数据失败: {ts_code}, 错误: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=200)
    def get_basic_info(self, ts_code: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取股票基本信息
        
        Args:
            ts_code: 股票代码，为None时获取所有股票
            
        Returns:
            DataFrame: 股票基本信息
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            df = self.pro.stock_basic(
                ts_code=ts_code,
                list_status='L',  # 只获取上市股票
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            if df.empty:
                logger.warning("未获取到股票基本信息")
                return None
            
            logger.info(f"获取股票基本信息成功，数量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=200)
    def get_daily_basic(self, ts_code: str, trade_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取每日基本面数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 YYYYMMDD
            
        Returns:
            DataFrame: 每日基本面数据
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            if trade_date:
                trade_date = trade_date.replace('-', '')
            
            df = self.pro.daily_basic(
                ts_code=ts_code,
                trade_date=trade_date,
                fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
            )
            
            if df.empty:
                logger.warning(f"未获取到每日基本面数据: {ts_code}")
                return None
            
            logger.info(f"获取每日基本面数据成功: {ts_code}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取每日基本面数据失败: {ts_code}, 错误: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=200)
    def get_money_flow(self, ts_code: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取资金流向数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            DataFrame: 资金流向数据
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            if start_date:
                start_date = start_date.replace('-', '')
            if end_date:
                end_date = end_date.replace('-', '')
            
            df = self.pro.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.warning(f"未获取到资金流向数据: {ts_code}")
                return None
            
            logger.info(f"获取资金流向数据成功: {ts_code}, 数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败: {ts_code}, 错误: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=200)
    def get_limit_list(self, trade_date: str, limit_type: str = 'U') -> Optional[pd.DataFrame]:
        """获取涨跌停股票列表
        
        Args:
            trade_date: 交易日期 YYYY-MM-DD
            limit_type: 涨跌停类型 U-涨停 D-跌停
            
        Returns:
            DataFrame: 涨跌停股票列表
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            trade_date = trade_date.replace('-', '')
            
            df = self.pro.limit_list(
                trade_date=trade_date,
                limit_type=limit_type
            )
            
            if df.empty:
                logger.warning(f"未获取到涨跌停数据: {trade_date}")
                return None
            
            logger.info(f"获取涨跌停数据成功: {trade_date}, 数量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {trade_date}, 错误: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=200)
    def get_top_list(self, trade_date: str, ts_code: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取龙虎榜数据
        
        Args:
            trade_date: 交易日期 YYYY-MM-DD
            ts_code: 股票代码
            
        Returns:
            DataFrame: 龙虎榜数据
        """
        if not self.is_available():
            logger.error("Tushare客户端不可用")
            return None
        
        try:
            trade_date = trade_date.replace('-', '')
            
            df = self.pro.top_list(
                trade_date=trade_date,
                ts_code=ts_code
            )
            
            if df.empty:
                logger.warning(f"未获取到龙虎榜数据: {trade_date}")
                return None
            
            logger.info(f"获取龙虎榜数据成功: {trade_date}, 数量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {trade_date}, 错误: {str(e)}")
            return None
    
    def convert_code_format(self, code: str, to_tushare: bool = True) -> str:
        """转换股票代码格式
        
        Args:
            code: 股票代码
            to_tushare: True-转换为Tushare格式，False-转换为通用格式
            
        Returns:
            str: 转换后的股票代码
        """
        if to_tushare:
            # 转换为Tushare格式 (如: 000001 -> 000001.SZ)
            if '.' not in code:
                if code.startswith('6'):
                    return f"{code}.SH"
                elif code.startswith(('0', '3')):
                    return f"{code}.SZ"
                elif code.startswith('4') or code.startswith('8'):
                    return f"{code}.BJ"
            return code
        else:
            # 转换为通用格式 (如: 000001.SZ -> 000001)
            return code.split('.')[0] if '.' in code else code
    
    def _process_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理日K线数据"""
        if df.empty:
            return df
        
        # 重命名列
        column_mapping = {
            'trade_date': 'date',
            'ts_code': 'code'
        }
        df = df.rename(columns=column_mapping)
        
        # 转换日期格式
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # 按日期排序
        df = df.sort_values('date')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df
    
    def _process_minute_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理分钟K线数据"""
        if df.empty:
            return df
        
        # 重命名列
        column_mapping = {
            'trade_time': 'datetime',
            'ts_code': 'code'
        }
        df = df.rename(columns=column_mapping)
        
        # 转换时间格式
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.strftime('%Y-%m-%d')
            df['time'] = df['datetime'].dt.strftime('%H:%M:%S')
        
        # 按时间排序
        df = df.sort_values('datetime')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df


# 创建全局实例
tushare_client = TushareClient()