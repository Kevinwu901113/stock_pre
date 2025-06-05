from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from config.database import get_db
from backend.app.models.stock import StockResponse
from backend.app.services.stock_service import StockService
from backend.app.core.response import success_response, error_response, paginated_response, convert_keys_to_camel
from loguru import logger

router = APIRouter()


@router.get("/search")
async def search_stocks(
    request: Request,
    q: str = Query(..., description="搜索关键词(股票代码或名称)"),
    market: Optional[str] = Query(None, description="市场筛选(SH/SZ)"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """搜索股票 - RESTful风格"""
    try:
        logger.info(f"接收到股票搜索请求 - q: {q}, market: {market}, industry: {industry}, page: {page}, size: {size}")
        
        service = StockService(db)
        
        # 使用现有的股票列表服务进行搜索
        stocks = await service.get_stock_list(
            market=market,
            industry=industry,
            search=q,
            page=page,
            size=size
        )
        
        # 转换字段名为camelCase
        items = [convert_keys_to_camel(stock.dict()) for stock in stocks.items]
        
        logger.info(f"搜索到 {stocks.total} 只股票，当前页 {len(stocks.items)} 条记录")
        return paginated_response(
            items=items,
            total=stocks.total,
            page=page,
            size=size,
            message="股票搜索成功"
        )
        
    except Exception as e:
        logger.error(f"股票搜索失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return error_response(message="股票搜索失败", code=500)


@router.get("/suggest")
async def suggest_stocks(
    request: Request,
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=20, description="建议数量"),
    db: Session = Depends(get_db)
):
    """股票搜索建议 - 用于自动补全"""
    try:
        logger.info(f"接收到股票建议请求 - q: {q}, limit: {limit}")
        
        service = StockService(db)
        
        # 获取建议列表（使用较小的页面大小）
        stocks = await service.get_stock_list(
            search=q,
            page=1,
            size=limit
        )
        
        # 简化返回数据，只包含基本信息
        suggestions = []
        for stock in stocks.items:
            suggestions.append({
                "code": stock.code,
                "name": stock.name,
                "market": stock.market,
                "industry": stock.industry
            })
        
        # 转换字段名为camelCase
        suggestions = [convert_keys_to_camel(item) for item in suggestions]
        
        logger.info(f"返回 {len(suggestions)} 条股票建议")
        return success_response(
            data=suggestions,
            message="获取股票建议成功"
        )
        
    except Exception as e:
        logger.error(f"获取股票建议失败: {str(e)}")
        return error_response(message="获取股票建议失败", code=500)