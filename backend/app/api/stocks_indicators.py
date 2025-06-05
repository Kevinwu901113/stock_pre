from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from config.database import get_db
from backend.app.services.stock_service import StockService
from backend.app.core.response import success_response, error_response, convert_keys_to_camel
from loguru import logger

router = APIRouter()


@router.get("/{stock_code}/indicators")
async def get_stock_indicators(
    stock_code: str,
    request: Request,
    indicators: str = Query("ma,macd,rsi,kdj", description="技术指标列表，逗号分隔: ma,macd,rsi,kdj,boll,cci,williams"),
    period: int = Query(20, ge=5, le=250, description="计算周期"),
    db: Session = Depends(get_db)
):
    """获取股票技术指标 - RESTful风格"""
    try:
        logger.info(f"接收到技术指标请求 - stock_code: {stock_code}, indicators: {indicators}, period: {period}")
        
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            return error_response(message="股票不存在", code=404)
        
        # 解析指标列表
        indicator_list = [ind.strip().lower() for ind in indicators.split(',')]
        
        # 获取技术指标数据（这里使用mock数据，实际应该计算真实指标）
        indicators_data = await _calculate_indicators(stock_code, indicator_list, period, service)
        
        # 转换字段名为camelCase
        indicators_data = convert_keys_to_camel(indicators_data)
        
        logger.info(f"返回股票 {stock_code} 的技术指标数据")
        return success_response(
            data={
                "stock_code": stock_code,
                "period": period,
                "indicators": indicators_data,
                "timestamp": datetime.now().isoformat()
            },
            message="获取技术指标成功"
        )
        
    except Exception as e:
        logger.error(f"获取技术指标失败: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return error_response(message="获取技术指标失败", code=500)


@router.get("/{stock_code}/indicators/ma")
async def get_stock_ma(
    stock_code: str,
    request: Request,
    periods: str = Query("5,10,20,60", description="MA周期列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """获取股票移动平均线指标"""
    try:
        logger.info(f"接收到MA指标请求 - stock_code: {stock_code}, periods: {periods}")
        
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            return error_response(message="股票不存在", code=404)
        
        # 解析周期列表
        period_list = [int(p.strip()) for p in periods.split(',')]
        
        # 计算MA指标（mock数据）
        ma_data = {}
        for period in period_list:
            ma_data[f"ma{period}"] = {
                "value": 10.25 + (period * 0.01),  # Mock数据
                "trend": "up" if period <= 20 else "down",
                "period": period
            }
        
        # 转换字段名为camelCase
        ma_data = convert_keys_to_camel(ma_data)
        
        logger.info(f"返回股票 {stock_code} 的MA指标数据")
        return success_response(
            data={
                "stock_code": stock_code,
                "ma_indicators": ma_data,
                "timestamp": datetime.now().isoformat()
            },
            message="获取MA指标成功"
        )
        
    except ValueError as e:
        logger.error(f"周期参数错误: {str(e)}")
        return error_response(message="周期参数格式错误", code=400)
    except Exception as e:
        logger.error(f"获取MA指标失败: {str(e)}")
        return error_response(message="获取MA指标失败", code=500)


@router.get("/{stock_code}/indicators/macd")
async def get_stock_macd(
    stock_code: str,
    request: Request,
    fast_period: int = Query(12, description="快线周期"),
    slow_period: int = Query(26, description="慢线周期"),
    signal_period: int = Query(9, description="信号线周期"),
    db: Session = Depends(get_db)
):
    """获取股票MACD指标"""
    try:
        logger.info(f"接收到MACD指标请求 - stock_code: {stock_code}")
        
        service = StockService(db)
        
        # 验证股票是否存在
        stock = await service.get_stock_detail(stock_code)
        if not stock:
            return error_response(message="股票不存在", code=404)
        
        # 计算MACD指标（mock数据）
        macd_data = {
            "dif": 0.15,  # Mock数据
            "dea": 0.12,
            "macd": 0.06,
            "signal": "buy",  # buy, sell, hold
            "trend": "bullish",  # bullish, bearish, neutral
            "parameters": {
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period
            }
        }
        
        # 转换字段名为camelCase
        macd_data = convert_keys_to_camel(macd_data)
        
        logger.info(f"返回股票 {stock_code} 的MACD指标数据")
        return success_response(
            data={
                "stock_code": stock_code,
                "macd_indicator": macd_data,
                "timestamp": datetime.now().isoformat()
            },
            message="获取MACD指标成功"
        )
        
    except Exception as e:
        logger.error(f"获取MACD指标失败: {str(e)}")
        return error_response(message="获取MACD指标失败", code=500)


async def _calculate_indicators(
    stock_code: str, 
    indicator_list: List[str], 
    period: int, 
    service: StockService
) -> Dict[str, Any]:
    """计算技术指标（mock实现）"""
    indicators_data = {}
    
    for indicator in indicator_list:
        if indicator == "ma":
            indicators_data["ma"] = {
                "ma5": 10.25,
                "ma10": 10.30,
                "ma20": 10.35,
                "ma60": 10.40
            }
        elif indicator == "macd":
            indicators_data["macd"] = {
                "dif": 0.15,
                "dea": 0.12,
                "macd": 0.06,
                "signal": "buy"
            }
        elif indicator == "rsi":
            indicators_data["rsi"] = {
                "rsi6": 65.5,
                "rsi12": 58.3,
                "rsi24": 52.1,
                "signal": "neutral"
            }
        elif indicator == "kdj":
            indicators_data["kdj"] = {
                "k": 75.2,
                "d": 68.9,
                "j": 87.8,
                "signal": "sell"
            }
        elif indicator == "boll":
            indicators_data["boll"] = {
                "upper": 10.80,
                "middle": 10.50,
                "lower": 10.20,
                "width": 0.60,
                "position": "middle"
            }
        elif indicator == "cci":
            indicators_data["cci"] = {
                "cci": 125.6,
                "signal": "overbought"
            }
        elif indicator == "williams":
            indicators_data["williams"] = {
                "wr": -25.8,
                "signal": "neutral"
            }
    
    return indicators_data