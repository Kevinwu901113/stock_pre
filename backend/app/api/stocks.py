from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from config.database import get_db
from backend.app.models.stock import (
    Stock, StockPrice, StockResponse, StockPriceResponse,
    StockListRequest, StockListResponse
)
from backend.app.services.stock_service import StockService
from backend.app.core.exceptions import ValidationException
from backend.app.core.response import success_response, error_response, paginated_response, convert_keys_to_camel
from loguru import logger

router = APIRouter()


@router.get("/")
async def get_stocks(
    request: Request,
    market: Optional[str] = Query(None, description="市场筛选(SH/SZ)"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    search: Optional[str] = Query(None, description="搜索关键词(代码或名称)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取股票列表 - RESTful风格"""
    try:
        logger.info(f"接收到股票列表请求 - market: {market}, industry: {industry}, search: {search}, page: {page}, size: {size}")
        
        service = StockService(db)
        stocks = await service.get_stock_list(
            market=market,
            industry=industry,
            search=search,
            page=page,
            size=size
        )
        
        # 转换字段名为camelCase
        items = [convert_keys_to_camel(stock.dict()) for stock in stocks.items]
        
        logger.info(f"成功返回 {stocks.total} 只股票，当前页 {len(stocks.items)} 条记录")
        return paginated_response(
            items=items,
            total=stocks.total,
            page=page,
            size=size,
            message="获取股票列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return error_response(message="获取股票列表失败", code=500)


@router.get("/{stock_code}")
async def get_stock(
    stock_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取股票详细信息 - RESTful风格"""
    try:
        service = StockService(db)
        stock = await service.get_stock_detail(stock_code)
        
        if not stock:
            return error_response(message="股票不存在", code=404)
        
        # 转换字段名为camelCase
        stock_data = convert_keys_to_camel(stock.dict())
        
        logger.info(f"返回股票 {stock_code} 的详细信息")
        return success_response(
            data=stock_data,
            message="获取股票信息成功"
        )
        
    except Exception as e:
        logger.error(f"获取股票信息失败: {str(e)}")
        return error_response(message="获取股票信息失败", code=500)


@router.get("/{stock_code}/price", response_model=List[StockPriceResponse])
async def get_stock_price_history(
    stock_code: str,
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取股票价格历史"""
    try:
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取价格历史
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        prices = await service.get_stock_price_history(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"返回股票 {stock_code} 的 {len(prices)} 条价格记录")
        return prices
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票价格历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取股票价格历史失败")


@router.get("/{stock_code}/current")
async def get_current_price(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取股票当前价格信息"""
    try:
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取当前价格信息
        current_info = await service.get_current_price_info(stock_code)
        
        logger.info(f"返回股票 {stock_code} 的当前价格信息")
        return current_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前价格失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取当前价格失败")


@router.get("/{stock_code}/technical")
async def get_technical_indicators(
    stock_code: str,
    period: int = Query(20, ge=5, le=250, description="计算周期"),
    db: Session = Depends(get_db)
):
    """获取股票技术指标"""
    try:
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取技术指标
        indicators = await service.get_technical_indicators(
            stock_code=stock_code,
            period=period
        )
        
        logger.info(f"返回股票 {stock_code} 的技术指标")
        return indicators
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取技术指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取技术指标失败")


@router.get("/{stock_code}/fundamental")
async def get_fundamental_data(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取股票基本面数据"""
    try:
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        
        # 获取基本面数据
        fundamental = await service.get_fundamental_data(stock_code)
        
        logger.info(f"返回股票 {stock_code} 的基本面数据")
        return fundamental
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基本面数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取基本面数据失败")


@router.get("/markets/summary")
async def get_market_summary(
    db: Session = Depends(get_db)
):
    """获取市场概况"""
    try:
        service = StockService(db)
        summary = await service.get_market_summary()
        
        logger.info("返回市场概况")
        return summary
        
    except Exception as e:
        logger.error(f"获取市场概况失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取市场概况失败")


@router.get("/industries/list")
async def get_industries(
    db: Session = Depends(get_db)
):
    """获取行业列表"""
    try:
        service = StockService(db)
        industries = await service.get_industries()
        
        logger.info(f"返回 {len(industries)} 个行业")
        return industries
        
    except Exception as e:
        logger.error(f"获取行业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取行业列表失败")


@router.get("/sectors/list")
async def get_sectors(
    db: Session = Depends(get_db)
):
    """获取板块列表"""
    try:
        service = StockService(db)
        sectors = await service.get_sectors()
        
        logger.info(f"返回 {len(sectors)} 个板块")
        return sectors
        
    except Exception as e:
        logger.error(f"获取板块列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取板块列表失败")


@router.get("/hot/gainers")
async def get_top_gainers(
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取涨幅榜"""
    try:
        service = StockService(db)
        gainers = await service.get_top_gainers(limit=limit)
        
        logger.info(f"返回涨幅榜前 {len(gainers)} 只股票")
        return gainers
        
    except Exception as e:
        logger.error(f"获取涨幅榜失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取涨幅榜失败")


@router.get("/hot/losers")
async def get_top_losers(
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取跌幅榜"""
    try:
        service = StockService(db)
        losers = await service.get_top_losers(limit=limit)
        
        logger.info(f"返回跌幅榜前 {len(losers)} 只股票")
        return losers
        
    except Exception as e:
        logger.error(f"获取跌幅榜失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取跌幅榜失败")


@router.get("/hot/volume")
async def get_top_volume(
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取成交量榜"""
    try:
        service = StockService(db)
        volume_leaders = await service.get_top_volume(limit=limit)
        
        logger.info(f"返回成交量榜前 {len(volume_leaders)} 只股票")
        return volume_leaders
        
    except Exception as e:
        logger.error(f"获取成交量榜失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取成交量榜失败")


@router.post("/sync")
async def sync_stock_data(
    stock_codes: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """同步股票数据"""
    try:
        service = StockService(db)
        result = await service.sync_stock_data(stock_codes=stock_codes)
        
        logger.info(f"股票数据同步完成: {result}")
        return {
            "message": "股票数据同步成功",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"股票数据同步失败: {str(e)}")
        raise HTTPException(status_code=500, detail="股票数据同步失败")