#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推荐接口端点
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from ...services.recommend_service import RecommendService
from ...services.data_service import DataService
from ...models.recommendation import RecommendationResult
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=dict)
async def get_recommendations(
    strategy_type: str = Query("evening_buy", description="策略类型: evening_buy, morning_sell"),
    trade_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    limit: int = Query(20, description="返回数量限制"),
    recommend_service: RecommendService = Depends(RecommendService),
    data_service: DataService = Depends(DataService)
):
    """获取当日尾盘推荐或早盘卖出列表"""
    try:
        logger.info(f"获取推荐列表: 策略={strategy_type}, 日期={trade_date}")
        
        # 参数验证
        if strategy_type not in ["evening_buy", "morning_sell"]:
            raise HTTPException(status_code=400, detail="不支持的策略类型")
        
        # 使用当前日期如果未指定
        if not trade_date:
            trade_date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取推荐结果
        recommendations = await recommend_service.get_recommendations(
            strategy_type=strategy_type,
            trade_date=trade_date,
            limit=limit
        )
        
        if not recommendations:
            return JSONResponse({
                "strategy_type": strategy_type,
                "trade_date": trade_date,
                "count": 0,
                "recommendations": [],
                "message": "暂无推荐结果"
            })
        
        # 转换为响应格式
        result = {
            "strategy_type": strategy_type,
            "trade_date": trade_date,
            "count": len(recommendations),
            "recommendations": [
                {
                    "code": rec.code,
                    "name": rec.name,
                    "score": rec.score,
                    "reason": rec.reason,
                    "price": rec.price,
                    "change_pct": rec.change_pct,
                    "volume": rec.volume,
                    "market_cap": rec.market_cap,
                    "pe_ratio": rec.pe_ratio,
                    "strategy_signals": rec.strategy_signals,
                    "risk_level": rec.risk_level,
                    "created_at": rec.created_at.isoformat() if rec.created_at else None
                }
                for rec in recommendations
            ],
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"推荐列表获取成功: {len(recommendations)}只股票")
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"获取推荐列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取推荐列表失败: {str(e)}")


@router.get("/history", response_model=dict)
async def get_recommendation_history(
    strategy_type: Optional[str] = Query(None, description="策略类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, description="返回数量限制"),
    recommend_service: RecommendService = Depends(RecommendService)
):
    """获取历史推荐记录"""
    try:
        logger.info(f"获取历史推荐: 策略={strategy_type}, 日期范围={start_date}~{end_date}")
        
        # 获取历史推荐
        history = await recommend_service.get_recommendation_history(
            strategy_type=strategy_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        result = {
            "strategy_type": strategy_type,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "count": len(history),
            "history": history
        }
        
        logger.info(f"历史推荐获取成功: {len(history)}条记录")
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"获取历史推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史推荐失败: {str(e)}")


@router.get("/performance", response_model=dict)
async def get_strategy_performance(
    strategy_type: str = Query(..., description="策略类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    recommend_service: RecommendService = Depends(RecommendService)
):
    """获取策略表现统计"""
    try:
        logger.info(f"获取策略表现: {strategy_type}")
        
        # 获取策略表现
        performance = await recommend_service.get_strategy_performance(
            strategy_type=strategy_type,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"策略表现获取成功: {strategy_type}")
        return JSONResponse(performance)
        
    except Exception as e:
        logger.error(f"获取策略表现失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略表现失败: {str(e)}")


@router.get("/history", response_model=dict)
async def get_recommendation_history(
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    type: Optional[str] = Query(None, description="推荐类型过滤"),
    recommend_service: RecommendService = Depends(RecommendService)
):
    """获取历史推荐记录"""
    try:
        logger.info(f"获取历史推荐: {start_date} 到 {end_date}, 类型={type}")
        
        history = await recommend_service.get_recommendation_history(
            start_date=start_date,
            end_date=end_date,
            recommendation_type=type
        )
        
        return JSONResponse(content={
            "start_date": start_date,
            "end_date": end_date,
            "type": type,
            "count": len(history),
            "history": history
        })
        
    except Exception as e:
        logger.error(f"获取历史推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史推荐失败: {str(e)}")


@router.get("/performance", response_model=dict)
async def get_recommendation_performance(
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    type: Optional[str] = Query(None, description="推荐类型过滤"),
    recommend_service: RecommendService = Depends(RecommendService)
):
    """获取推荐策略表现统计"""
    try:
        logger.info(f"获取推荐表现: {start_date} 到 {end_date}, 类型={type}")
        
        performance = await recommend_service.get_recommendation_performance(
            start_date=start_date,
            end_date=end_date,
            recommendation_type=type
        )
        
        return JSONResponse(content=performance)
        
    except Exception as e:
        logger.error(f"获取推荐表现失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取推荐表现失败: {str(e)}")


@router.post("/generate", response_model=dict)
async def generate_recommendations(
    type: str = Query(..., description="推荐类型: buy, sell"),
    force: bool = Query(False, description="是否强制重新生成"),
    recommend_service: RecommendService = Depends(RecommendService)
):
    """手动生成推荐"""
    try:
        logger.info(f"手动生成推荐: 类型={type}, 强制={force}")
        
        if type not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="推荐类型必须是 buy 或 sell")
        
        result = await recommend_service.generate_recommendations(
            recommendation_type=type,
            force_regenerate=force
        )
        
        return JSONResponse(content={
            "message": "推荐生成完成",
            "type": type,
            "generated_count": result.get("count", 0),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"生成推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成推荐失败: {str(e)}")


@router.get("/status", response_model=dict)
async def get_recommendation_status(
    recommend_service: RecommendService = Depends(RecommendService)
):
    """获取推荐系统状态"""
    try:
        status = await recommend_service.get_system_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"获取推荐状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/explain/{code}", response_model=dict)
async def explain_recommendation(
    code: str,
    date: Optional[str] = Query(None, description="推荐日期 YYYY-MM-DD"),
    recommend_service: RecommendService = Depends(RecommendService)
):
    """解释推荐理由"""
    try:
        logger.info(f"解释推荐理由: {code}, 日期={date}")
        
        explanation = await recommend_service.explain_recommendation(
            stock_code=code,
            recommendation_date=date
        )
        
        if not explanation:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的推荐记录")
        
        return JSONResponse(content=explanation)
        
    except Exception as e:
        logger.error(f"解释推荐理由失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解释推荐失败: {str(e)}")