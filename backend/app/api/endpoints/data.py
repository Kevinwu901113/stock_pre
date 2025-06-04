#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据接口端点
"""

from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from ...services.data_service import DataService
from ...models.stock import StockData, StockInfo
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/stock/{code}", response_model=dict)
async def get_stock_data(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    period: str = Query("daily", description="数据周期: daily, minute"),
    data_service: DataService = Depends(DataService)
):
    """获取指定股票的历史行情数据"""
    try:
        logger.info(f"获取股票数据: {code}, 周期: {period}")
        
        # 参数验证
        if not code:
            raise HTTPException(status_code=400, detail="股票代码不能为空")
        
        # 获取数据
        data = await data_service.get_stock_data(
            code=code,
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的数据")
        
        # 转换为JSON格式
        result = {
            "code": code,
            "period": period,
            "count": len(data),
            "data": data.to_dict("records")
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取股票数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/stock/{code}/info", response_model=dict)
async def get_stock_info(
    code: str,
    data_service: DataService = Depends(DataService)
):
    """获取股票基本信息"""
    try:
        logger.info(f"获取股票信息: {code}")
        
        info = await data_service.get_stock_info(code)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的信息")
        
        return JSONResponse(content=info)
        
    except Exception as e:
        logger.error(f"获取股票信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")


@router.get("/market/overview", response_model=dict)
async def get_market_overview(
    data_service: DataService = Depends(DataService)
):
    """获取市场概览数据"""
    try:
        logger.info("获取市场概览数据")
        
        overview = await data_service.get_market_overview()
        
        return JSONResponse(content=overview)
        
    except Exception as e:
        logger.error(f"获取市场概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


@router.get("/stocks/search", response_model=dict)
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, description="返回数量限制"),
    data_service: DataService = Depends(DataService)
):
    """搜索股票"""
    try:
        logger.info(f"搜索股票: {keyword}")
        
        results = await data_service.search_stocks(keyword, limit)
        
        return JSONResponse(content={
            "keyword": keyword,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        logger.error(f"搜索股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/indicators/{code}", response_model=dict)
async def get_technical_indicators(
    code: str,
    indicators: List[str] = Query(["ma5", "ma20", "rsi", "macd"], description="技术指标列表"),
    period: int = Query(30, description="计算周期"),
    data_service: DataService = Depends(DataService)
):
    """获取技术指标数据"""
    try:
        logger.info(f"获取技术指标: {code}, 指标: {indicators}")
        
        indicator_data = await data_service.get_technical_indicators(
            code=code,
            indicators=indicators,
            period=period
        )
        
        return JSONResponse(content={
            "code": code,
            "indicators": indicators,
            "period": period,
            "data": indicator_data
        })
        
    except Exception as e:
        logger.error(f"获取技术指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")


@router.post("/upload/csv")
async def upload_csv_data(
    # 这里可以添加文件上传逻辑
    data_service: DataService = Depends(DataService)
):
    """上传CSV数据文件"""
    try:
        # TODO: 实现CSV文件上传和解析逻辑
        return JSONResponse(content={
            "message": "CSV上传功能待实现",
            "status": "pending"
        })
        
    except Exception as e:
        logger.error(f"上传CSV失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/cache/status")
async def get_cache_status(
    data_service: DataService = Depends(DataService)
):
    """获取缓存状态"""
    try:
        status = await data_service.get_cache_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"获取缓存状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取缓存状态失败: {str(e)}")


@router.delete("/cache/clear")
async def clear_cache(
    data_service: DataService = Depends(DataService)
):
    """清除缓存"""
    try:
        await data_service.clear_cache()
        return JSONResponse(content={"message": "缓存已清除"})
        
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")