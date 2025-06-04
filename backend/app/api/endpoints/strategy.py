#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略接口端点
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from fastapi.responses import JSONResponse

from ...services.strategy_service import StrategyService
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/list", response_model=dict)
async def list_strategies(
    strategy_service: StrategyService = Depends(StrategyService)
):
    """获取所有可用策略列表"""
    try:
        logger.info("获取策略列表")
        
        strategies = await strategy_service.list_strategies()
        
        return JSONResponse(content={
            "count": len(strategies),
            "strategies": strategies
        })
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/{strategy_name}", response_model=dict)
async def get_strategy_info(
    strategy_name: str,
    strategy_service: StrategyService = Depends(StrategyService)
):
    """获取指定策略的详细信息"""
    try:
        logger.info(f"获取策略信息: {strategy_name}")
        
        strategy_info = await strategy_service.get_strategy_info(strategy_name)
        
        if not strategy_info:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        
        return JSONResponse(content=strategy_info)
        
    except Exception as e:
        logger.error(f"获取策略信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略信息失败: {str(e)}")


@router.get("/{strategy_name}/config", response_model=dict)
async def get_strategy_config(
    strategy_name: str,
    strategy_service: StrategyService = Depends(StrategyService)
):
    """获取策略配置"""
    try:
        logger.info(f"获取策略配置: {strategy_name}")
        
        config = await strategy_service.get_strategy_config(strategy_name)
        
        if config is None:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        
        return JSONResponse(content={
            "strategy_name": strategy_name,
            "config": config
        })
        
    except Exception as e:
        logger.error(f"获取策略配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.put("/{strategy_name}/config", response_model=dict)
async def update_strategy_config(
    strategy_name: str,
    config: Dict[str, Any] = Body(...),
    strategy_service: StrategyService = Depends(StrategyService)
):
    """更新策略配置"""
    try:
        logger.info(f"更新策略配置: {strategy_name}")
        
        success = await strategy_service.update_strategy_config(strategy_name, config)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
        
        return JSONResponse(content={
            "message": f"策略 {strategy_name} 配置更新成功",
            "strategy_name": strategy_name,
            "config": config
        })
        
    except Exception as e:
        logger.error(f"更新策略配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")


@router.post("/{strategy_name}/run", response_model=dict)
async def run_strategy(
    strategy_name: str,
    params: Optional[Dict[str, Any]] = Body(None),
    strategy_service: StrategyService = Depends(StrategyService)
):
    """运行指定策略"""
    try:
        logger.info(f"运行策略: {strategy_name}")
        
        result = await strategy_service.run_strategy(strategy_name, params)
        
        return JSONResponse(content={
            "message": f"策略 {strategy_name} 运行完成",
            "strategy_name": strategy_name,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"运行策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"运行策略失败: {str(e)}")


@router.post("/{strategy_name}/backtest", response_model=dict)
async def backtest_strategy(
    strategy_name: str,
    start_date: str = Body(...),
    end_date: str = Body(...),
    params: Optional[Dict[str, Any]] = Body(None),
    strategy_service: StrategyService = Depends(StrategyService)
):
    """策略回测"""
    try:
        logger.info(f"策略回测: {strategy_name}, {start_date} 到 {end_date}")
        
        backtest_result = await strategy_service.backtest_strategy(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            params=params
        )
        
        return JSONResponse(content={
            "strategy_name": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "backtest_result": backtest_result
        })
        
    except Exception as e:
        logger.error(f"策略回测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"策略回测失败: {str(e)}")


@router.get("/{strategy_name}/performance", response_model=dict)
async def get_strategy_performance(
    strategy_name: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    strategy_service: StrategyService = Depends(StrategyService)
):
    """获取策略表现统计"""
    try:
        logger.info(f"获取策略表现: {strategy_name}")
        
        performance = await strategy_service.get_strategy_performance(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date
        )
        
        return JSONResponse(content={
            "strategy_name": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "performance": performance
        })
        
    except Exception as e:
        logger.error(f"获取策略表现失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略表现失败: {str(e)}")


@router.post("/compare", response_model=dict)
async def compare_strategies(
    strategy_names: List[str] = Body(...),
    start_date: str = Body(...),
    end_date: str = Body(...),
    strategy_service: StrategyService = Depends(StrategyService)
):
    """策略对比分析"""
    try:
        logger.info(f"策略对比: {strategy_names}")
        
        comparison = await strategy_service.compare_strategies(
            strategy_names=strategy_names,
            start_date=start_date,
            end_date=end_date
        )
        
        return JSONResponse(content={
            "strategy_names": strategy_names,
            "start_date": start_date,
            "end_date": end_date,
            "comparison": comparison
        })
        
    except Exception as e:
        logger.error(f"策略对比失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"策略对比失败: {str(e)}")


@router.get("/schedule/status", response_model=dict)
async def get_schedule_status(
    strategy_service: StrategyService = Depends(StrategyService)
):
    """获取策略调度状态"""
    try:
        logger.info("获取策略调度状态")
        
        status = await strategy_service.get_schedule_status()
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"获取调度状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取调度状态失败: {str(e)}")


@router.post("/schedule/start", response_model=dict)
async def start_schedule(
    strategy_service: StrategyService = Depends(StrategyService)
):
    """启动策略调度"""
    try:
        logger.info("启动策略调度")
        
        success = await strategy_service.start_schedule()
        
        return JSONResponse(content={
            "message": "策略调度已启动" if success else "策略调度启动失败",
            "status": "running" if success else "failed"
        })
        
    except Exception as e:
        logger.error(f"启动策略调度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动调度失败: {str(e)}")


@router.post("/schedule/stop", response_model=dict)
async def stop_schedule(
    strategy_service: StrategyService = Depends(StrategyService)
):
    """停止策略调度"""
    try:
        logger.info("停止策略调度")
        
        success = await strategy_service.stop_schedule()
        
        return JSONResponse(content={
            "message": "策略调度已停止" if success else "策略调度停止失败",
            "status": "stopped" if success else "failed"
        })
        
    except Exception as e:
        logger.error(f"停止策略调度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止调度失败: {str(e)}")