from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from config.database import get_db
from backend.app.models.stock import StrategyResultResponse, StrategyType
from backend.app.services.strategy_service import StrategyService
from backend.app.core.exceptions import ValidationException, StrategyException
from loguru import logger

router = APIRouter()


@router.get("/")
async def get_strategies(
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型"),
    enabled_only: bool = Query(True, description="仅返回启用的策略"),
    db: Session = Depends(get_db)
):
    """获取策略列表（根路径）"""
    try:
        service = StrategyService(db)
        strategies = await service.get_strategy_list(
            strategy_type=strategy_type,
            enabled_only=enabled_only
        )
        
        logger.info(f"返回 {len(strategies)} 个策略")
        return strategies
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略列表失败")


@router.get("/list")
async def get_strategy_list(
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型"),
    enabled_only: bool = Query(True, description="仅返回启用的策略"),
    db: Session = Depends(get_db)
):
    """获取策略列表"""
    try:
        service = StrategyService(db)
        strategies = await service.get_strategy_list(
            strategy_type=strategy_type,
            enabled_only=enabled_only
        )
        
        logger.info(f"返回 {len(strategies)} 个策略")
        return strategies
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略列表失败")


@router.get("/{strategy_name}")
async def get_strategy_info(
    strategy_name: str,
    db: Session = Depends(get_db)
):
    """获取策略详细信息"""
    try:
        service = StrategyService(db)
        strategy_info = await service.get_strategy_info(strategy_name)
        
        if not strategy_info:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        logger.info(f"返回策略 {strategy_name} 的详细信息")
        return strategy_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略信息失败")


@router.get("/{strategy_name}/config")
async def get_strategy_config(
    strategy_name: str,
    db: Session = Depends(get_db)
):
    """获取策略配置"""
    try:
        service = StrategyService(db)
        config = await service.get_strategy_config(strategy_name)
        
        if not config:
            raise HTTPException(status_code=404, detail="策略配置不存在")
        
        logger.info(f"返回策略 {strategy_name} 的配置")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略配置失败")


@router.put("/{strategy_name}/config")
async def update_strategy_config(
    strategy_name: str,
    config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新策略配置"""
    try:
        service = StrategyService(db)
        
        # 验证配置
        await service.validate_strategy_config(strategy_name, config)
        
        # 更新配置
        result = await service.update_strategy_config(strategy_name, config)
        
        logger.info(f"策略 {strategy_name} 配置更新成功")
        return {
            "message": "策略配置更新成功",
            "strategy_name": strategy_name,
            "config": result
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StrategyException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新策略配置失败")


@router.post("/{strategy_name}/execute")
async def execute_strategy(
    strategy_name: str,
    stock_codes: Optional[List[str]] = None,
    force: bool = Query(False, description="强制执行(忽略缓存)"),
    db: Session = Depends(get_db)
):
    """执行策略"""
    try:
        service = StrategyService(db)
        
        # 执行策略
        result = await service.execute_strategy(
            strategy_name=strategy_name,
            stock_codes=stock_codes,
            force=force
        )
        
        logger.info(f"策略 {strategy_name} 执行完成")
        return {
            "message": "策略执行成功",
            "strategy_name": strategy_name,
            "result": result
        }
        
    except StrategyException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"执行策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail="执行策略失败")


@router.get("/{strategy_name}/results", response_model=List[StrategyResultResponse])
async def get_strategy_results(
    strategy_name: str,
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    stock_code: Optional[str] = Query(None, description="股票代码筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取策略执行结果"""
    try:
        service = StrategyService(db)
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = await service.get_strategy_results(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            stock_code=stock_code,
            page=page,
            size=size
        )
        
        logger.info(f"返回策略 {strategy_name} 的 {len(results)} 条结果")
        return results
        
    except Exception as e:
        logger.error(f"获取策略结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略结果失败")


@router.get("/{strategy_name}/performance")
async def get_strategy_performance(
    strategy_name: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取策略表现统计"""
    try:
        service = StrategyService(db)
        performance = await service.get_strategy_performance(
            strategy_name=strategy_name,
            days=days
        )
        
        logger.info(f"返回策略 {strategy_name} 的表现统计")
        return performance
        
    except Exception as e:
        logger.error(f"获取策略表现失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取策略表现失败")


@router.get("/{strategy_name}/backtest")
async def run_strategy_backtest(
    strategy_name: str,
    start_date: datetime = Query(..., description="回测开始日期"),
    end_date: datetime = Query(..., description="回测结束日期"),
    stock_codes: Optional[List[str]] = Query(None, description="股票代码列表"),
    initial_capital: float = Query(100000, description="初始资金"),
    db: Session = Depends(get_db)
):
    """运行策略回测"""
    try:
        # 验证日期范围
        if start_date >= end_date:
            raise ValidationException("开始日期必须早于结束日期")
        
        # 限制回测时间范围(最多1年)
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise ValidationException(f"回测时间范围不能超过{max_days}天")
        
        service = StrategyService(db)
        backtest_result = await service.run_backtest(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            stock_codes=stock_codes,
            initial_capital=initial_capital
        )
        
        logger.info(f"策略 {strategy_name} 回测完成")
        return backtest_result
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StrategyException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"策略回测失败: {str(e)}")
        raise HTTPException(status_code=500, detail="策略回测失败")


@router.post("/combine")
async def create_combined_strategy(
    name: str,
    strategies: List[Dict[str, Any]],
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建组合策略"""
    try:
        service = StrategyService(db)
        
        # 验证策略组合
        await service.validate_strategy_combination(strategies)
        
        # 创建组合策略
        result = await service.create_combined_strategy(
            name=name,
            strategies=strategies,
            description=description
        )
        
        logger.info(f"组合策略 {name} 创建成功")
        return {
            "message": "组合策略创建成功",
            "strategy_name": name,
            "result": result
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StrategyException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"创建组合策略失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建组合策略失败")


@router.get("/compare/performance")
async def compare_strategies(
    strategy_names: List[str] = Query(..., description="策略名称列表"),
    days: int = Query(30, ge=1, le=365, description="比较天数"),
    db: Session = Depends(get_db)
):
    """比较多个策略的表现"""
    try:
        if len(strategy_names) > 10:
            raise ValidationException("最多只能比较10个策略")
        
        service = StrategyService(db)
        comparison = await service.compare_strategies(
            strategy_names=strategy_names,
            days=days
        )
        
        logger.info(f"策略比较完成，比较了 {len(strategy_names)} 个策略")
        return comparison
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"策略比较失败: {str(e)}")
        raise HTTPException(status_code=500, detail="策略比较失败")


@router.post("/optimize/{strategy_name}")
async def optimize_strategy(
    strategy_name: str,
    optimization_params: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """优化策略参数"""
    try:
        service = StrategyService(db)
        
        # 运行参数优化
        optimization_result = await service.optimize_strategy_parameters(
            strategy_name=strategy_name,
            optimization_params=optimization_params
        )
        
        logger.info(f"策略 {strategy_name} 参数优化完成")
        return optimization_result
        
    except StrategyException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"策略参数优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail="策略参数优化失败")