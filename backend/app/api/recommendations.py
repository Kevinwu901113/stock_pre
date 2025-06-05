from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from config.database import get_db
from app.models.stock import (
    Recommendation, Stock, StockPrice,
    RecommendationResponse, RecommendationWithStock,
    RecommendationListRequest, RecommendationType,
    RecommendationListResponse
)
from app.services.recommendation_service import RecommendationService
from app.core.exceptions import ValidationException
from loguru import logger

router = APIRouter()


@router.get("/buy", response_model=List[RecommendationWithStock])
async def get_buy_recommendations(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    min_confidence: float = Query(0.6, ge=0, le=1, description="最小置信度"),
    strategy: Optional[str] = Query(None, description="策略筛选"),
    db: Session = Depends(get_db)
):
    """获取买入推荐列表"""
    try:
        service = RecommendationService(db)
        recommendations = await service.get_active_recommendations(
            recommendation_type=RecommendationType.BUY,
            limit=limit,
            min_confidence=min_confidence,
            strategy_name=strategy
        )
        
        logger.info(f"返回 {len(recommendations)} 条买入推荐")
        return recommendations
        
    except Exception as e:
        logger.error(f"获取买入推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取买入推荐失败")


@router.get("/sell", response_model=List[RecommendationWithStock])
async def get_sell_recommendations(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    min_confidence: float = Query(0.6, ge=0, le=1, description="最小置信度"),
    strategy: Optional[str] = Query(None, description="策略筛选"),
    db: Session = Depends(get_db)
):
    """获取卖出推荐列表"""
    try:
        service = RecommendationService(db)
        recommendations = await service.get_active_recommendations(
            recommendation_type=RecommendationType.SELL,
            limit=limit,
            min_confidence=min_confidence,
            strategy_name=strategy
        )
        
        logger.info(f"返回 {len(recommendations)} 条卖出推荐")
        return recommendations
        
    except Exception as e:
        logger.error(f"获取卖出推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取卖出推荐失败")


@router.get("/today", response_model=List[RecommendationWithStock])
async def get_today_recommendations(
    recommendation_type: Optional[RecommendationType] = Query(None, description="推荐类型"),
    strategy: Optional[str] = Query(None, description="策略筛选"),
    db: Session = Depends(get_db)
):
    """获取今日推荐"""
    try:
        service = RecommendationService(db)
        
        # 获取今日推荐
        today = datetime.now().date()
        recommendations = await service.get_recommendations_by_date(
            date=today,
            recommendation_type=recommendation_type,
            strategy_name=strategy
        )
        
        logger.info(f"返回今日 {len(recommendations)} 条推荐")
        return recommendations
        
    except Exception as e:
        logger.error(f"获取今日推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取今日推荐失败")


@router.get("/history", response_model=RecommendationListResponse)
async def get_historical_recommendations(
    date_from: datetime = Query(..., description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    recommendation_type: Optional[RecommendationType] = Query(None, description="推荐类型"),
    strategy: Optional[str] = Query(None, description="策略筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取历史推荐"""
    try:
        # 验证日期范围
        if date_to is None:
            date_to = datetime.now()
        
        if date_from > date_to:
            raise ValidationException("开始日期不能大于结束日期")
        
        # 限制查询范围(最多查询90天)
        max_days = 90
        if (date_to - date_from).days > max_days:
            raise ValidationException(f"查询范围不能超过{max_days}天")
        
        service = RecommendationService(db)
        result = await service.get_historical_recommendations_paginated(
            date_from=date_from,
            date_to=date_to,
            recommendation_type=recommendation_type,
            strategy_name=strategy,
            page=page,
            size=size
        )
        
        logger.info(f"返回历史推荐 {len(result['items'])} 条，总计 {result['total']} 条")
        return result
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"获取历史推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史推荐失败")


@router.get("/stock/{stock_code}", response_model=List[RecommendationResponse])
async def get_stock_recommendations(
    stock_code: str,
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取特定股票的推荐历史"""
    try:
        service = RecommendationService(db)
        
        # 验证股票代码
        stock = db.query(Stock).filter(Stock.code == stock_code).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取推荐历史
        date_from = datetime.now() - timedelta(days=days)
        recommendations = await service.get_stock_recommendations(
            stock_code=stock_code,
            date_from=date_from
        )
        
        logger.info(f"返回股票 {stock_code} 的 {len(recommendations)} 条推荐")
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取股票推荐失败")


@router.get("/strategies", response_model=List[str])
async def get_available_strategies(
    db: Session = Depends(get_db)
):
    """获取可用的策略列表"""
    try:
        service = RecommendationService(db)
        strategies = await service.get_available_strategies()
        
        logger.info(f"返回 {len(strategies)} 个可用策略")
        return strategies
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略列表失败")


@router.get("/performance/{strategy_name}")
async def get_strategy_performance(
    strategy_name: str,
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取策略表现统计"""
    try:
        service = RecommendationService(db)
        performance = await service.get_strategy_performance(
            strategy_name=strategy_name,
            days=days
        )
        
        logger.info(f"返回策略 {strategy_name} 的表现统计")
        return performance
        
    except Exception as e:
        logger.error(f"获取策略表现失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略表现失败")


@router.post("/refresh")
async def refresh_recommendations(
    strategy: Optional[str] = Query(None, description="指定策略"),
    db: Session = Depends(get_db)
):
    """手动刷新推荐(触发策略执行)"""
    try:
        service = RecommendationService(db)
        result = await service.refresh_recommendations(strategy_name=strategy)
        
        logger.info(f"推荐刷新完成: {result}")
        return {
            "message": "推荐刷新成功",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"推荐刷新失败: {str(e)}")
        raise HTTPException(status_code=500, detail="推荐刷新失败")


@router.get("/summary")
async def get_recommendations_summary(
    db: Session = Depends(get_db)
):
    """获取推荐汇总信息"""
    try:
        service = RecommendationService(db)
        summary = await service.get_recommendations_summary()
        
        logger.info("返回推荐汇总信息")
        return summary
        
    except Exception as e:
        logger.error(f"获取推荐汇总失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取推荐汇总失败")