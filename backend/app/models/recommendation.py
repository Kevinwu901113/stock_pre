#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐数据模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class RecommendationType(str, Enum):
    """推荐类型"""
    BUY = "buy"           # 买入推荐
    SELL = "sell"         # 卖出推荐
    HOLD = "hold"         # 持有推荐
    WATCH = "watch"       # 观望推荐


class RecommendationLevel(str, Enum):
    """推荐等级"""
    STRONG_BUY = "strong_buy"     # 强烈买入
    BUY = "buy"                   # 买入
    WEAK_BUY = "weak_buy"         # 弱买入
    HOLD = "hold"                 # 持有
    WEAK_SELL = "weak_sell"       # 弱卖出
    SELL = "sell"                 # 卖出
    STRONG_SELL = "strong_sell"   # 强烈卖出


class RecommendationStatus(str, Enum):
    """推荐状态"""
    ACTIVE = "active"       # 活跃
    EXECUTED = "executed"   # 已执行
    EXPIRED = "expired"     # 已过期
    CANCELLED = "cancelled" # 已取消


class Recommendation(BaseModel):
    """推荐记录"""
    id: Optional[str] = Field(None, description="推荐ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    recommendation_type: RecommendationType = Field(..., description="推荐类型")
    recommendation_level: RecommendationLevel = Field(..., description="推荐等级")
    strategy_name: str = Field(..., description="策略名称")
    target_price: Optional[float] = Field(None, description="目标价格")
    current_price: float = Field(..., description="当前价格")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    take_profit_price: Optional[float] = Field(None, description="止盈价格")
    confidence_score: float = Field(..., description="置信度评分 (0-100)")
    expected_return: Optional[float] = Field(None, description="预期收益率 (%)")
    risk_level: Optional[int] = Field(None, description="风险等级 (1-5)")
    recommendation_date: date = Field(..., description="推荐日期")
    expiry_date: Optional[date] = Field(None, description="过期日期")
    status: RecommendationStatus = Field(default=RecommendationStatus.ACTIVE, description="推荐状态")
    reason: str = Field(..., description="推荐理由")
    technical_signals: Optional[Dict[str, Any]] = Field(None, description="技术信号")
    fundamental_data: Optional[Dict[str, Any]] = Field(None, description="基本面数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }


class RecommendationFilter(BaseModel):
    """推荐筛选条件"""
    recommendation_type: Optional[RecommendationType] = Field(None, description="推荐类型")
    recommendation_level: Optional[RecommendationLevel] = Field(None, description="推荐等级")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    min_confidence: Optional[float] = Field(None, description="最小置信度")
    max_risk_level: Optional[int] = Field(None, description="最大风险等级")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    status: Optional[RecommendationStatus] = Field(None, description="推荐状态")
    stock_codes: Optional[List[str]] = Field(None, description="股票代码列表")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class RecommendationPerformance(BaseModel):
    """推荐表现统计"""
    strategy_name: str = Field(..., description="策略名称")
    total_recommendations: int = Field(..., description="总推荐数")
    successful_recommendations: int = Field(..., description="成功推荐数")
    success_rate: float = Field(..., description="成功率 (%)")
    average_return: float = Field(..., description="平均收益率 (%)")
    max_return: float = Field(..., description="最大收益率 (%)")
    min_return: float = Field(..., description="最小收益率 (%)")
    total_return: float = Field(..., description="总收益率 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤 (%)")
    win_rate: float = Field(..., description="胜率 (%)")
    profit_loss_ratio: Optional[float] = Field(None, description="盈亏比")
    start_date: date = Field(..., description="统计开始日期")
    end_date: date = Field(..., description="统计结束日期")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class RecommendationExplanation(BaseModel):
    """推荐解释"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    recommendation_type: RecommendationType = Field(..., description="推荐类型")
    strategy_name: str = Field(..., description="策略名称")
    main_reason: str = Field(..., description="主要推荐理由")
    technical_analysis: Dict[str, Any] = Field(..., description="技术分析")
    fundamental_analysis: Optional[Dict[str, Any]] = Field(None, description="基本面分析")
    risk_factors: List[str] = Field(..., description="风险因素")
    key_indicators: Dict[str, float] = Field(..., description="关键指标")
    market_context: Optional[str] = Field(None, description="市场环境")
    similar_cases: Optional[List[Dict[str, Any]]] = Field(None, description="相似案例")
    ai_insight: Optional[str] = Field(None, description="AI洞察")
    confidence_breakdown: Dict[str, float] = Field(..., description="置信度分解")
    

class RecommendationRequest(BaseModel):
    """推荐请求"""
    recommendation_type: RecommendationType = Field(..., description="推荐类型")
    target_date: Optional[date] = Field(None, description="目标日期")
    strategy_names: Optional[List[str]] = Field(None, description="指定策略列表")
    stock_pool: Optional[List[str]] = Field(None, description="股票池")
    limit: int = Field(default=20, description="返回数量限制")
    min_confidence: float = Field(default=60.0, description="最小置信度")
    force_regenerate: bool = Field(default=False, description="强制重新生成")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class RecommendationResponse(BaseModel):
    """推荐响应"""
    recommendation_type: RecommendationType = Field(..., description="推荐类型")
    target_date: date = Field(..., description="目标日期")
    total_count: int = Field(..., description="总数量")
    recommendations: List[Recommendation] = Field(..., description="推荐列表")
    generation_time: datetime = Field(default_factory=datetime.now, description="生成时间")
    strategy_summary: Dict[str, int] = Field(..., description="策略汇总")
    market_summary: Optional[Dict[str, Any]] = Field(None, description="市场汇总")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }


class BacktestResult(BaseModel):
    """回测结果"""
    strategy_name: str = Field(..., description="策略名称")
    start_date: date = Field(..., description="回测开始日期")
    end_date: date = Field(..., description="回测结束日期")
    total_trades: int = Field(..., description="总交易次数")
    winning_trades: int = Field(..., description="盈利交易次数")
    losing_trades: int = Field(..., description="亏损交易次数")
    win_rate: float = Field(..., description="胜率 (%)")
    total_return: float = Field(..., description="总收益率 (%)")
    annual_return: float = Field(..., description="年化收益率 (%)")
    max_drawdown: float = Field(..., description="最大回撤 (%)")
    sharpe_ratio: float = Field(..., description="夏普比率")
    volatility: float = Field(..., description="波动率 (%)")
    benchmark_return: Optional[float] = Field(None, description="基准收益率 (%)")
    alpha: Optional[float] = Field(None, description="阿尔法")
    beta: Optional[float] = Field(None, description="贝塔")
    trade_details: List[Dict[str, Any]] = Field(..., description="交易明细")
    equity_curve: List[Dict[str, Any]] = Field(..., description="净值曲线")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }