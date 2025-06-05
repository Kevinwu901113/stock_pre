from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

# 导入共享的Base
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.database import Base


class RecommendationType(str, Enum):
    """推荐类型枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyType(str, Enum):
    """策略类型枚举"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    COMBINED = "combined"


# SQLAlchemy模型
class Stock(Base):
    """股票基础信息表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)  # 股票代码
    name = Column(String(50), nullable=False)  # 股票名称
    market = Column(String(10), nullable=False)  # 市场(SH/SZ)
    industry = Column(String(50))  # 行业
    sector = Column(String(50))  # 板块
    list_date = Column(DateTime)  # 上市日期
    is_active = Column(Boolean, default=True)  # 是否活跃
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_stock_code_market', 'code', 'market'),
    )


class StockPrice(Base):
    """股票价格数据表"""
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)  # 成交量
    amount = Column(Float)  # 成交额
    turnover_rate = Column(Float)  # 换手率
    pe_ratio = Column(Float)  # 市盈率
    pb_ratio = Column(Float)  # 市净率
    market_cap = Column(Float)  # 总市值
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_price_code_date', 'stock_code', 'trade_date'),
    )


class Recommendation(Base):
    """推荐记录表"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    recommendation_type = Column(String(10), nullable=False)  # buy/sell/hold
    strategy_name = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 置信度分数
    target_price = Column(Float)  # 目标价格
    stop_loss_price = Column(Float)  # 止损价格
    reason = Column(Text)  # 推荐理由
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # 推荐过期时间
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_rec_code_type_date', 'stock_code', 'recommendation_type', 'created_at'),
    )


class StrategyResult(Base):
    """策略执行结果表"""
    __tablename__ = "strategy_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String(50), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    execution_date = Column(DateTime, nullable=False, index=True)
    signal_type = Column(String(10))  # buy/sell/hold
    signal_strength = Column(Float)  # 信号强度
    parameters = Column(Text)  # 策略参数(JSON)
    result_data = Column(Text)  # 结果数据(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_strategy_name_date', 'strategy_name', 'execution_date'),
    )


# Pydantic模型(API请求/响应)
class StockBase(BaseModel):
    """股票基础模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")
    industry: Optional[str] = Field(None, description="行业")
    sector: Optional[str] = Field(None, description="板块")


class StockCreate(StockBase):
    """创建股票模型"""
    list_date: Optional[datetime] = Field(None, description="上市日期")


class StockResponse(StockBase):
    """股票响应模型"""
    id: int
    list_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # 价格相关字段
    market_cap: Optional[float] = Field(None, description="总市值")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    current_price: Optional[float] = Field(None, description="当前价格")
    price_change: Optional[float] = Field(None, description="价格变化")
    price_change_percent: Optional[float] = Field(None, description="价格变化百分比")
    volume: Optional[float] = Field(None, description="成交量")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    
    class Config:
        from_attributes = True


class StockPriceBase(BaseModel):
    """股票价格基础模型"""
    stock_code: str = Field(..., description="股票代码")
    trade_date: datetime = Field(..., description="交易日期")
    open_price: Optional[float] = Field(None, description="开盘价")
    high_price: Optional[float] = Field(None, description="最高价")
    low_price: Optional[float] = Field(None, description="最低价")
    close_price: Optional[float] = Field(None, description="收盘价")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    market_cap: Optional[float] = Field(None, description="总市值")


class StockPriceResponse(StockPriceBase):
    """股票价格响应模型"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationBase(BaseModel):
    """推荐基础模型"""
    stock_code: str = Field(..., description="股票代码")
    recommendation_type: RecommendationType = Field(..., description="推荐类型")
    strategy_name: str = Field(..., description="策略名称")
    confidence_score: float = Field(..., ge=0, le=1, description="置信度分数")
    target_price: Optional[float] = Field(None, description="目标价格")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    reason: Optional[str] = Field(None, description="推荐理由")


class RecommendationCreate(RecommendationBase):
    """创建推荐模型"""
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class RecommendationResponse(RecommendationBase):
    """推荐响应模型"""
    id: int
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class RecommendationWithStock(RecommendationResponse):
    """包含股票信息的推荐模型"""
    stock_name: str = Field(..., description="股票名称")
    current_price: Optional[float] = Field(None, description="当前价格")
    price_change: Optional[float] = Field(None, description="价格变化")
    price_change_percent: Optional[float] = Field(None, description="价格变化百分比")


class StrategyResultBase(BaseModel):
    """策略结果基础模型"""
    strategy_name: str = Field(..., description="策略名称")
    stock_code: str = Field(..., description="股票代码")
    execution_date: datetime = Field(..., description="执行日期")
    signal_type: Optional[str] = Field(None, description="信号类型")
    signal_strength: Optional[float] = Field(None, description="信号强度")
    parameters: Optional[str] = Field(None, description="策略参数")
    result_data: Optional[str] = Field(None, description="结果数据")


class StrategyResultResponse(StrategyResultBase):
    """策略结果响应模型"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockListRequest(BaseModel):
    """股票列表请求模型"""
    market: Optional[str] = Field(None, description="市场筛选")
    industry: Optional[str] = Field(None, description="行业筛选")
    sector: Optional[str] = Field(None, description="板块筛选")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


class RecommendationListRequest(BaseModel):
    """推荐列表请求模型"""
    recommendation_type: Optional[RecommendationType] = Field(None, description="推荐类型")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    min_confidence: Optional[float] = Field(None, ge=0, le=1, description="最小置信度")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


class StockListResponse(BaseModel):
    """股票列表响应模型"""
    items: List[StockResponse] = Field(..., description="股票列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class PaginatedResponse(BaseModel):
    """分页响应基础模型"""
    items: List = Field(..., description="数据列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class RecommendationListResponse(BaseModel):
    """推荐列表响应模型"""
    items: List[RecommendationWithStock] = Field(..., description="推荐列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class MarketOverview(BaseModel):
    """市场概览模型"""
    total_stocks: int = Field(..., description="股票总数")
    active_stocks: int = Field(..., description="活跃股票数")
    rising_stocks: int = Field(..., description="上涨股票数")
    falling_stocks: int = Field(..., description="下跌股票数")
    unchanged_stocks: int = Field(..., description="平盘股票数")
    total_market_cap: Optional[float] = Field(None, description="总市值")
    avg_pe_ratio: Optional[float] = Field(None, description="平均市盈率")
    avg_turnover_rate: Optional[float] = Field(None, description="平均换手率")
    last_updated: datetime = Field(..., description="最后更新时间")


class TechnicalIndicators(BaseModel):
    """技术指标模型"""
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    rsi: Optional[float] = Field(None, description="RSI指标")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_histogram: Optional[float] = Field(None, description="MACD柱状图")
    kdj_k: Optional[float] = Field(None, description="KDJ-K值")
    kdj_d: Optional[float] = Field(None, description="KDJ-D值")
    kdj_j: Optional[float] = Field(None, description="KDJ-J值")
    bollinger_upper: Optional[float] = Field(None, description="布林带上轨")
    bollinger_middle: Optional[float] = Field(None, description="布林带中轨")
    bollinger_lower: Optional[float] = Field(None, description="布林带下轨")
    volume_ratio: Optional[float] = Field(None, description="量比")
    turnover_rate: Optional[float] = Field(None, description="换手率")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    calculated_at: datetime = Field(..., description="计算时间")