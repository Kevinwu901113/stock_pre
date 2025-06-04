#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略数据模型
"""

from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class StrategyType(str, Enum):
    """策略类型"""
    TECHNICAL = "technical"       # 技术分析策略
    FUNDAMENTAL = "fundamental"   # 基本面策略
    SENTIMENT = "sentiment"       # 情绪分析策略
    HYBRID = "hybrid"             # 混合策略
    CUSTOM = "custom"             # 自定义策略


class StrategyTimeframe(str, Enum):
    """策略时间框架"""
    INTRADAY = "intraday"         # 日内策略
    DAILY = "daily"               # 日线策略
    WEEKLY = "weekly"             # 周线策略
    MONTHLY = "monthly"           # 月线策略


class StrategyDirection(str, Enum):
    """策略方向"""
    LONG = "long"                 # 做多策略
    SHORT = "short"               # 做空策略
    BOTH = "both"                 # 双向策略


class StrategyStatus(str, Enum):
    """策略状态"""
    ACTIVE = "active"             # 活跃
    INACTIVE = "inactive"         # 非活跃
    TESTING = "testing"           # 测试中
    DEPRECATED = "deprecated"     # 已弃用


class StrategyInfo(BaseModel):
    """策略信息"""
    name: str = Field(..., description="策略名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    timeframe: StrategyTimeframe = Field(..., description="时间框架")
    direction: StrategyDirection = Field(..., description="策略方向")
    status: StrategyStatus = Field(default=StrategyStatus.ACTIVE, description="策略状态")
    version: str = Field(default="1.0.0", description="策略版本")
    author: Optional[str] = Field(None, description="策略作者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    tags: List[str] = Field(default=[], description="标签")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StrategyParameter(BaseModel):
    """策略参数"""
    name: str = Field(..., description="参数名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="参数描述")
    param_type: str = Field(..., description="参数类型")
    default_value: Any = Field(..., description="默认值")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    step: Optional[float] = Field(None, description="步长")
    options: Optional[List[Any]] = Field(None, description="选项列表")
    required: bool = Field(default=True, description="是否必需")


class StrategyConfig(BaseModel):
    """策略配置"""
    strategy_name: str = Field(..., description="策略名称")
    enabled: bool = Field(default=True, description="是否启用")
    run_time: Optional[str] = Field(None, description="运行时间")
    params: Dict[str, Any] = Field(default={}, description="参数配置")
    stock_pool: Optional[List[str]] = Field(None, description="股票池")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    max_positions: Optional[int] = Field(None, description="最大持仓数")
    risk_control: Optional[Dict[str, Any]] = Field(None, description="风险控制")
    notification: Optional[Dict[str, Any]] = Field(None, description="通知配置")


class StrategySignal(BaseModel):
    """策略信号"""
    strategy_name: str = Field(..., description="策略名称")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    signal_type: str = Field(..., description="信号类型")
    signal_strength: float = Field(..., description="信号强度")
    price: float = Field(..., description="信号价格")
    volume: Optional[float] = Field(None, description="信号成交量")
    timestamp: datetime = Field(default_factory=datetime.now, description="信号时间")
    indicators: Dict[str, Any] = Field(default={}, description="指标数据")
    description: Optional[str] = Field(None, description="信号描述")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StrategyPerformance(BaseModel):
    """策略表现"""
    strategy_name: str = Field(..., description="策略名称")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    total_signals: int = Field(..., description="总信号数")
    valid_signals: int = Field(..., description="有效信号数")
    accuracy_rate: float = Field(..., description="准确率 (%)")
    average_return: float = Field(..., description="平均收益率 (%)")
    total_return: float = Field(..., description="总收益率 (%)")
    max_drawdown: float = Field(..., description="最大回撤 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    win_rate: float = Field(..., description="胜率 (%)")
    profit_loss_ratio: Optional[float] = Field(None, description="盈亏比")
    daily_statistics: Optional[Dict[str, Any]] = Field(None, description="每日统计")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class StrategyComparison(BaseModel):
    """策略对比"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    strategies: List[str] = Field(..., description="策略列表")
    benchmark: Optional[str] = Field(None, description="基准指标")
    performance_metrics: Dict[str, Dict[str, float]] = Field(..., description="表现指标")
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = Field(None, description="相关性矩阵")
    equity_curves: Dict[str, List[Dict[str, Any]]] = Field(..., description="净值曲线")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class ScheduleStatus(BaseModel):
    """调度状态"""
    is_running: bool = Field(..., description="是否运行中")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    last_run_time: Optional[datetime] = Field(None, description="上次运行时间")
    active_strategies: List[str] = Field(..., description="活跃策略")
    job_count: int = Field(..., description="任务数量")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }