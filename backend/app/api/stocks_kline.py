from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from config.database import get_db
from backend.app.models.stock import StockPriceResponse
from backend.app.services.stock_service import StockService
from backend.app.core.response import success_response, error_response, convert_keys_to_camel
from loguru import logger

router = APIRouter()


@router.get("/{stock_code}/kline")
async def get_stock_kline(
    stock_code: str,
    request: Request,
    period: str = Query("1d", description="K线周期: 1d(日线), 1w(周线), 1m(月线)"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取股票K线数据 - RESTful风格"""
    try:
        logger.info(f"接收到K线数据请求 - stock_code: {stock_code}, period: {period}, start_date: {start_date}, end_date: {end_date}")
        
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            return error_response(message="股票不存在", code=404)
        
        # 处理日期参数
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
            
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # 默认获取最近的数据
            if period == "1d":
                start_dt = end_dt - timedelta(days=limit)
            elif period == "1w":
                start_dt = end_dt - timedelta(weeks=limit)
            elif period == "1m":
                start_dt = end_dt - timedelta(days=limit * 30)
            else:
                start_dt = end_dt - timedelta(days=limit)
        
        # 获取价格历史数据
        prices = await service.get_stock_price_history(
            stock_code=stock_code,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # 根据周期处理数据（这里简化处理，实际应该根据周期聚合数据）
        kline_data = []
        for price in prices[:limit]:  # 限制返回数量
            kline_item = {
                "timestamp": price.trade_date.isoformat(),
                "open": price.open_price,
                "high": price.high_price,
                "low": price.low_price,
                "close": price.close_price,
                "volume": price.volume,
                "amount": price.amount,
                "turnover_rate": price.turnover_rate
            }
            kline_data.append(kline_item)
        
        # 转换字段名为camelCase
        kline_data = [convert_keys_to_camel(item) for item in kline_data]
        
        logger.info(f"返回股票 {stock_code} 的 {len(kline_data)} 条K线数据")
        return success_response(
            data={
                "stockCode": stock_code,
                "period": period,
                "klineData": kline_data,
                "count": len(kline_data)
            },
            message="获取K线数据成功"
        )
        
    except ValueError as e:
        logger.error(f"日期格式错误: {str(e)}")
        return error_response(message="日期格式错误，请使用YYYY-MM-DD格式", code=400)
    except Exception as e:
        logger.error(f"获取K线数据失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return error_response(message="获取K线数据失败", code=500)


@router.get("/{stock_code}/realtime")
async def get_stock_realtime(
    stock_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取股票实时数据"""
    try:
        logger.info(f"接收到实时数据请求 - stock_code: {stock_code}")
        
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            return error_response(message="股票不存在", code=404)
        
        # 获取当前价格信息（这里使用mock数据，实际应该调用实时数据接口）
        realtime_data = {
            "stock_code": stock_code,
            "name": stock.name,
            "current_price": 10.50,  # Mock数据
            "price_change": 0.25,
            "change_percent": 2.44,
            "volume": 1234567,
            "amount": 12987654.32,
            "turnover_rate": 1.23,
            "high_price": 10.68,
            "low_price": 10.15,
            "open_price": 10.25,
            "pre_close": 10.25,
            "market_cap": 5432109876.54,
            "pe_ratio": 15.67,
            "pb_ratio": 1.89,
            "timestamp": datetime.now().isoformat(),
            "status": "trading"  # trading, suspended, closed
        }
        
        # 转换字段名为camelCase
        realtime_data = convert_keys_to_camel(realtime_data)
        
        logger.info(f"返回股票 {stock_code} 的实时数据")
        return success_response(
            data=realtime_data,
            message="获取实时数据成功"
        )
        
    except Exception as e:
        logger.error(f"获取实时数据失败: {str(e)}")
        return error_response(message="获取实时数据失败", code=500)