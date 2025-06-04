#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class MarketType(str, Enum):
    """市场类型"""
    SH = "SH"  # 上海证券交易所
    SZ = "SZ"  # 深圳证券交易所
    BJ = "BJ"  # 北京证券交易所


class StockType(str, Enum):
    """股票类型"""
    STOCK = "stock"        # 普通股票
    INDEX = "index"        # 指数
    ETF = "etf"           # ETF基金
    BOND = "bond"         # 债券


class StockInfo(BaseModel):
    """股票基本信息"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: MarketType = Field(..., description="所属市场")
    stock_type: StockType = Field(default=StockType.STOCK, description="股票类型")
    industry: Optional[str] = Field(None, description="所属行业")
    sector: Optional[str] = Field(None, description="所属板块")
    list_date: Optional[date] = Field(None, description="上市日期")
    market_cap: Optional[float] = Field(None, description="总市值（万元）")
    float_cap: Optional[float] = Field(None, description="流通市值（万元）")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    is_active: bool = Field(default=True, description="是否活跃交易")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class StockData(BaseModel):
    """股票行情数据"""
    code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    pre_close: Optional[float] = Field(None, description="前收盘价")
    volume: float = Field(..., description="成交量（手）")
    amount: float = Field(..., description="成交额（元）")
    turnover_rate: Optional[float] = Field(None, description="换手率（%）")
    change: Optional[float] = Field(None, description="涨跌额")
    pct_change: Optional[float] = Field(None, description="涨跌幅（%）")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class MinuteData(BaseModel):
    """分钟级行情数据"""
    code: str = Field(..., description="股票代码")
    datetime: datetime = Field(..., description="时间戳")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TechnicalIndicator(BaseModel):
    """技术指标数据"""
    code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    rsi: Optional[float] = Field(None, description="RSI指标")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_hist: Optional[float] = Field(None, description="MACD柱状图")
    kdj_k: Optional[float] = Field(None, description="KDJ-K值")
    kdj_d: Optional[float] = Field(None, description="KDJ-D值")
    kdj_j: Optional[float] = Field(None, description="KDJ-J值")
    boll_upper: Optional[float] = Field(None, description="布林带上轨")
    boll_mid: Optional[float] = Field(None, description="布林带中轨")
    boll_lower: Optional[float] = Field(None, description="布林带下轨")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class MarketOverview(BaseModel):
    """市场概览数据"""
    trade_date: date = Field(..., description="交易日期")
    total_stocks: int = Field(..., description="总股票数")
    up_stocks: int = Field(..., description="上涨股票数")
    down_stocks: int = Field(..., description="下跌股票数")
    flat_stocks: int = Field(..., description="平盘股票数")
    limit_up_stocks: int = Field(..., description="涨停股票数")
    limit_down_stocks: int = Field(..., description="跌停股票数")
    total_volume: float = Field(..., description="总成交量")
    total_amount: float = Field(..., description="总成交额")
    avg_pct_change: float = Field(..., description="平均涨跌幅")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class StockFilter(BaseModel):
    """股票筛选条件"""
    min_price: Optional[float] = Field(None, description="最低价格")
    max_price: Optional[float] = Field(None, description="最高价格")
    min_market_cap: Optional[float] = Field(None, description="最小市值（亿元）")
    max_market_cap: Optional[float] = Field(None, description="最大市值（亿元）")
    min_volume: Optional[float] = Field(None, description="最小成交量")
    min_turnover_rate: Optional[float] = Field(None, description="最小换手率")
    max_turnover_rate: Optional[float] = Field(None, description="最大换手率")
    industries: Optional[List[str]] = Field(None, description="行业过滤")
    exclude_st: bool = Field(default=True, description="排除ST股票")
    exclude_new: bool = Field(default=True, description="排除新股（上市30天内）")
    min_list_days: Optional[int] = Field(None, description="最少上市天数")


class DataSource(str, Enum):
    """数据源类型"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    SINA = "sina"
    EASTMONEY = "eastmoney"
    CSV = "csv"
    LOCAL = "local"


class DataRequest(BaseModel):
    """数据请求模型"""
    code: str = Field(..., description="股票代码")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    period: str = Field(default="daily", description="数据周期")
    source: DataSource = Field(default=DataSource.TUSHARE, description="数据源")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    

class DataResponse(BaseModel):
    """数据响应模型"""
    code: str = Field(..., description="股票代码")
    source: DataSource = Field(..., description="数据源")
    period: str = Field(..., description="数据周期")
    count: int = Field(..., description="数据条数")
    from_cache: bool = Field(default=False, description="是否来自缓存")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    data: List[Dict[str, Any]] = Field(..., description="数据内容")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }