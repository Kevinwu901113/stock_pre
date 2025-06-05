from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from config.database import get_db
from backend.app.models.stock import (
    Recommendation, Stock, RecommendationType,
    RecommendationResponse
)
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.strategy_service import StrategyService
from loguru import logger

router = APIRouter()

def execute_strategy_task(request_data: dict) -> dict:
    """执行策略任务（同步版本，供调度器调用）"""
    try:
        # 获取数据库会话
        db = next(get_db())
        
        try:
            strategy_type = request_data.get('strategy_type')
            parameters = request_data.get('parameters', {})
            
            # 获取活跃股票代码
            stock_codes = get_active_stock_codes_sync(db)
            
            if not stock_codes:
                return {'recommendations': [], 'message': '没有找到活跃股票'}
            
            # 执行策略
            strategy_service = StrategyService(db)
            results = strategy_service.execute_strategy_sync(
                strategy_name=strategy_type,
                stock_codes=stock_codes,
                parameters=parameters
            )
            
            # 保存推荐结果
            saved_recommendations = []
            for result in results:
                if result.get('confidence', 0) >= parameters.get('min_confidence', 0.6):
                    recommendation = Recommendation(
                        stock_code=result['stock_code'],
                        recommendation_type=result['signal'],
                        strategy_name=strategy_type,
                        confidence_score=result['confidence'],
                        target_price=result.get('target_price'),
                        stop_loss_price=result.get('stop_loss'),
                        reason=result.get('reason', ''),
                        signal_type=result.get('signal_type'),
                        expected_return=result.get('expected_return'),
                        holding_period=result.get('holding_period'),
                        risk_level=result.get('risk_level', 'medium'),
                        created_at=datetime.now(),
                        expires_at=result.get('expires_at'),
                        is_active=True
                    )
                    
                    db.add(recommendation)
                    saved_recommendations.append({
                        'stock_code': result['stock_code'],
                        'signal': result['signal'],
                        'confidence': result['confidence'],
                        'reason': result.get('reason', '')
                    })
            
            db.commit()
            
            return {
                'recommendations': saved_recommendations,
                'message': f'成功生成 {len(saved_recommendations)} 条推荐'
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"执行策略任务失败: {str(e)}")
        return {'recommendations': [], 'error': str(e)}


def get_active_stock_codes_sync(db) -> List[str]:
    """同步获取活跃股票代码"""
    try:
        stocks = db.query(Stock).filter(
            Stock.is_active == True
        ).limit(1000).all()
        
        return [stock.code for stock in stocks]
        
    except Exception as e:
        logger.error(f"获取活跃股票失败: {str(e)}")
        return []


class GenerateRecommendationRequest(BaseModel):
    """生成推荐请求模型"""
    strategy_name: str = Field(..., description="策略名称")
    stock_codes: Optional[List[str]] = Field(None, description="指定股票代码列表，为空则使用全市场")
    max_recommendations: int = Field(10, ge=1, le=50, description="最大推荐数量")
    min_confidence: float = Field(0.6, ge=0.1, le=1.0, description="最小置信度")
    force_generate: bool = Field(False, description="是否强制生成（忽略时间限制）")


class GenerateRecommendationResponse(BaseModel):
    """生成推荐响应模型"""
    success: bool
    message: str
    generated_count: int
    recommendations: List[RecommendationResponse]
    execution_time: float


class ScheduledTaskRequest(BaseModel):
    """定时任务请求模型"""
    task_type: str = Field(..., description="任务类型：end_of_day_buy 或 morning_exit")
    force_run: bool = Field(False, description="是否强制执行")


@router.post("/generate", response_model=GenerateRecommendationResponse)
async def generate_recommendations(
    request: GenerateRecommendationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """生成推荐
    
    根据指定策略生成买入或卖出推荐，支持：
    - 尾盘买入策略
    - 早盘卖出策略
    - 其他技术分析策略
    """
    start_time = datetime.now()
    
    try:
        # 验证策略名称
        strategy_service = StrategyService(db)
        available_strategies = await strategy_service.get_strategies()
        strategy_names = [s['name'] for s in available_strategies]
        
        if request.strategy_name not in strategy_names:
            raise HTTPException(
                status_code=400, 
                detail=f"策略 '{request.strategy_name}' 不存在。可用策略: {strategy_names}"
            )
        
        # 检查时间限制（除非强制生成）
        if not request.force_generate:
            time_check = _check_trading_time(request.strategy_name)
            if not time_check['allowed']:
                raise HTTPException(
                    status_code=400,
                    detail=time_check['message']
                )
        
        # 获取股票代码列表
        if request.stock_codes:
            stock_codes = request.stock_codes
        else:
            # 获取活跃股票列表
            stock_codes = await _get_active_stock_codes(db)
        
        logger.info(f"开始执行策略 {request.strategy_name}，股票数量: {len(stock_codes)}")
        
        # 执行策略
        strategy_results = await strategy_service.execute_strategy(
            strategy_name=request.strategy_name,
            stock_codes=stock_codes,
            parameters={}
        )
        
        # 过滤和排序结果
        filtered_results = [
            result for result in strategy_results 
            if result.get('confidence', 0) >= request.min_confidence
        ]
        
        # 按置信度排序并限制数量
        filtered_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        filtered_results = filtered_results[:request.max_recommendations]
        
        # 保存推荐到数据库
        recommendation_service = RecommendationService(db)
        saved_recommendations = []
        
        for result in filtered_results:
            try:
                # 创建推荐记录
                recommendation = Recommendation(
                    stock_code=result['stock_code'],
                    recommendation_type=result['signal'],
                    strategy_name=result.get('strategy_name', request.strategy_name),
                    confidence_score=result['confidence'],
                    target_price=result.get('target_price'),
                    stop_loss_price=result.get('stop_loss'),
                    reason=result.get('reason', ''),
                    created_at=datetime.now(),
                    expires_at=result.get('expires_at'),
                    is_active=True
                )
                
                db.add(recommendation)
                db.flush()  # 获取ID
                
                # 转换为响应模型
                rec_response = RecommendationResponse(
                    id=recommendation.id,
                    stock_code=recommendation.stock_code,
                    recommendation_type=recommendation.recommendation_type,
                    strategy_name=recommendation.strategy_name,
                    confidence_score=recommendation.confidence_score,
                    target_price=recommendation.target_price,
                    stop_loss_price=recommendation.stop_loss_price,
                    reason=recommendation.reason,
                    created_at=recommendation.created_at,
                    expires_at=recommendation.expires_at,
                    is_active=recommendation.is_active
                )
                
                saved_recommendations.append(rec_response)
                
            except Exception as e:
                logger.error(f"保存推荐失败 {result['stock_code']}: {str(e)}")
                continue
        
        # 提交事务
        db.commit()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"策略 {request.strategy_name} 执行完成，"
            f"生成推荐 {len(saved_recommendations)} 条，"
            f"耗时 {execution_time:.2f} 秒"
        )
        
        return GenerateRecommendationResponse(
            success=True,
            message=f"成功生成 {len(saved_recommendations)} 条推荐",
            generated_count=len(saved_recommendations),
            recommendations=saved_recommendations,
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"生成推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成推荐失败: {str(e)}")


@router.post("/scheduled-task")
async def run_scheduled_task(
    request: ScheduledTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """执行定时任务
    
    支持的任务类型：
    - end_of_day_buy: 尾盘买入推荐生成
    - morning_exit: 早盘卖出推荐生成
    """
    try:
        if request.task_type == "end_of_day_buy":
            # 尾盘买入任务
            if not request.force_run and not _is_end_of_day_time():
                raise HTTPException(
                    status_code=400,
                    detail="当前不是尾盘时间（14:30-15:00），请使用 force_run=true 强制执行"
                )
            
            # 在后台执行尾盘买入策略
            background_tasks.add_task(
                _execute_end_of_day_strategy, db
            )
            
            return {
                "success": True,
                "message": "尾盘买入任务已启动",
                "task_type": request.task_type
            }
            
        elif request.task_type == "morning_exit":
            # 早盘卖出任务
            if not request.force_run and not _is_morning_time():
                raise HTTPException(
                    status_code=400,
                    detail="当前不是早盘时间（9:30-10:00），请使用 force_run=true 强制执行"
                )
            
            # 在后台执行早盘卖出策略
            background_tasks.add_task(
                _execute_morning_exit_strategy, db
            )
            
            return {
                "success": True,
                "message": "早盘卖出任务已启动",
                "task_type": request.task_type
            }
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的任务类型: {request.task_type}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行定时任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行定时任务失败: {str(e)}")


@router.get("/active")
async def get_active_recommendations(
    recommendation_type: Optional[RecommendationType] = None,
    strategy_name: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取当前活跃的推荐"""
    try:
        service = RecommendationService(db)
        
        if recommendation_type:
            recommendations = await service.get_active_recommendations(
                recommendation_type=recommendation_type,
                limit=limit,
                strategy_name=strategy_name
            )
        else:
            # 获取所有类型的活跃推荐
            buy_recs = await service.get_active_recommendations(
                recommendation_type=RecommendationType.BUY,
                limit=limit//2,
                strategy_name=strategy_name
            )
            sell_recs = await service.get_active_recommendations(
                recommendation_type=RecommendationType.SELL,
                limit=limit//2,
                strategy_name=strategy_name
            )
            recommendations = buy_recs + sell_recs
        
        return {
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"获取活跃推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取活跃推荐失败")


# 辅助函数

def _check_trading_time(strategy_name: str) -> Dict[str, Any]:
    """检查交易时间"""
    now = datetime.now()
    current_time = now.time()
    
    if strategy_name == "end_of_day":
        # 尾盘策略：14:30-15:00
        if not _is_end_of_day_time():
            return {
                "allowed": False,
                "message": "尾盘策略只能在14:30-15:00执行"
            }
    elif strategy_name == "morning_exit":
        # 早盘策略：9:30-10:00
        if not _is_morning_time():
            return {
                "allowed": False,
                "message": "早盘策略只能在9:30-10:00执行"
            }
    
    return {"allowed": True, "message": "时间检查通过"}


def _is_end_of_day_time() -> bool:
    """检查是否为尾盘时间"""
    now = datetime.now()
    current_time = now.time()
    
    # 14:30-15:00
    start_time = datetime.strptime("14:30", "%H:%M").time()
    end_time = datetime.strptime("15:00", "%H:%M").time()
    
    return start_time <= current_time <= end_time


def _is_morning_time() -> bool:
    """检查是否为早盘时间"""
    now = datetime.now()
    current_time = now.time()
    
    # 9:30-10:00
    start_time = datetime.strptime("09:30", "%H:%M").time()
    end_time = datetime.strptime("10:00", "%H:%M").time()
    
    return start_time <= current_time <= end_time


async def _get_active_stock_codes(db: Session) -> List[str]:
    """获取活跃股票代码列表"""
    try:
        stocks = db.query(Stock).filter(Stock.is_active == True).limit(1000).all()
        return [stock.code for stock in stocks]
    except Exception as e:
        logger.error(f"获取股票代码列表失败: {str(e)}")
        return []


async def _execute_end_of_day_strategy(db: Session):
    """执行尾盘买入策略（后台任务）"""
    try:
        logger.info("开始执行尾盘买入策略")
        
        # 获取股票代码
        stock_codes = await _get_active_stock_codes(db)
        
        # 执行策略
        strategy_service = StrategyService(db)
        results = await strategy_service.execute_strategy(
            strategy_name="end_of_day",
            stock_codes=stock_codes,
            parameters={}
        )
        
        # 保存推荐
        saved_count = 0
        for result in results:
            if result.get('confidence', 0) >= 0.7:  # 高置信度推荐
                try:
                    recommendation = Recommendation(
                        stock_code=result['stock_code'],
                        recommendation_type=result['signal'],
                        strategy_name='end_of_day',
                        confidence_score=result['confidence'],
                        target_price=result.get('target_price'),
                        stop_loss_price=result.get('stop_loss'),
                        reason=result.get('reason', ''),
                        created_at=datetime.now(),
                        expires_at=result.get('expires_at'),
                        is_active=True
                    )
                    
                    db.add(recommendation)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"保存尾盘推荐失败 {result['stock_code']}: {str(e)}")
                    continue
        
        db.commit()
        logger.info(f"尾盘买入策略执行完成，生成推荐 {saved_count} 条")
        
    except Exception as e:
        db.rollback()
        logger.error(f"执行尾盘买入策略失败: {str(e)}")


async def _execute_morning_exit_strategy(db: Session):
    """执行早盘卖出策略（后台任务）"""
    try:
        logger.info("开始执行早盘卖出策略")
        
        # 获取昨日买入的股票
        yesterday = datetime.now().date() - timedelta(days=1)
        
        held_stocks = db.query(Recommendation).filter(
            and_(
                Recommendation.recommendation_type == 'buy',
                Recommendation.created_at >= yesterday,
                Recommendation.is_active == True
            )
        ).all()
        
        stock_codes = [rec.stock_code for rec in held_stocks]
        
        if not stock_codes:
            logger.info("没有持有股票，跳过早盘卖出策略")
            return
        
        # 执行策略
        strategy_service = StrategyService(db)
        results = await strategy_service.execute_strategy(
            strategy_name="morning_exit",
            stock_codes=stock_codes,
            parameters={}
        )
        
        # 保存卖出推荐
        saved_count = 0
        for result in results:
            if result.get('confidence', 0) >= 0.6:  # 卖出推荐
                try:
                    recommendation = Recommendation(
                        stock_code=result['stock_code'],
                        recommendation_type=result['signal'],
                        strategy_name='morning_exit',
                        confidence_score=result['confidence'],
                        target_price=result.get('current_price'),
                        reason=result.get('reason', ''),
                        created_at=datetime.now(),
                        expires_at=result.get('expires_at'),
                        is_active=True
                    )
                    
                    db.add(recommendation)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"保存早盘卖出推荐失败 {result['stock_code']}: {str(e)}")
                    continue
        
        db.commit()
        logger.info(f"早盘卖出策略执行完成，生成推荐 {saved_count} 条")
        
    except Exception as e:
        db.rollback()
        logger.error(f"执行早盘卖出策略失败: {str(e)}")