from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import io

from config.database import get_db
from app.services.data_service import DataService
from app.core.exceptions import ValidationException, DataSourceException
from loguru import logger

router = APIRouter()


@router.get("/sources")
async def get_data_sources(
    db: Session = Depends(get_db)
):
    """获取可用的数据源列表"""
    try:
        service = DataService(db)
        sources = await service.get_available_data_sources()
        
        logger.info(f"返回 {len(sources)} 个数据源")
        return sources
        
    except Exception as e:
        logger.error(f"获取数据源列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据源列表失败")


@router.get("/sources/{source_name}/status")
async def get_data_source_status(
    source_name: str,
    db: Session = Depends(get_db)
):
    """获取数据源状态"""
    try:
        service = DataService(db)
        status = await service.get_data_source_status(source_name)
        
        if not status:
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        logger.info(f"返回数据源 {source_name} 的状态")
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据源状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据源状态失败")


@router.post("/sync")
async def sync_market_data(
    source: Optional[str] = Query(None, description="指定数据源"),
    stock_codes: Optional[List[str]] = Query(None, description="指定股票代码"),
    data_type: Optional[str] = Query(None, description="数据类型(daily/minute/fundamental)"),
    force: bool = Query(False, description="强制同步(忽略缓存)"),
    db: Session = Depends(get_db)
):
    """同步市场数据"""
    try:
        service = DataService(db)
        
        result = await service.sync_market_data(
            source=source,
            stock_codes=stock_codes,
            data_type=data_type,
            force=force
        )
        
        logger.info(f"市场数据同步完成: {result}")
        return {
            "message": "市场数据同步成功",
            "result": result
        }
        
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"市场数据同步失败: {str(e)}")
        raise HTTPException(status_code=500, detail="市场数据同步失败")


@router.get("/kline/{stock_code}")
async def get_kline_data(
    stock_code: str,
    period: str = Query("daily", description="周期(daily/minute/5min/15min/30min/60min)"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """获取K线数据"""
    try:
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 验证日期范围
        if start_date >= end_date:
            raise ValidationException("开始日期必须早于结束日期")
        
        service = DataService(db)
        kline_data = await service.get_kline_data(
            stock_code=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        logger.info(f"返回股票 {stock_code} 的 {len(kline_data)} 条K线数据")
        return kline_data
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"获取K线数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取K线数据失败")


@router.get("/realtime/{stock_code}")
async def get_realtime_data(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取实时行情数据"""
    try:
        service = DataService(db)
        realtime_data = await service.get_realtime_data(stock_code)
        
        if not realtime_data:
            raise HTTPException(status_code=404, detail="未找到实时数据")
        
        logger.info(f"返回股票 {stock_code} 的实时数据")
        return realtime_data
        
    except HTTPException:
        raise
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"获取实时数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取实时数据失败")


@router.get("/fundamental/{stock_code}")
async def get_fundamental_data(
    stock_code: str,
    report_type: str = Query("annual", description="报告类型(annual/quarterly)"),
    years: int = Query(3, ge=1, le=10, description="年份数量"),
    db: Session = Depends(get_db)
):
    """获取基本面数据"""
    try:
        service = DataService(db)
        fundamental_data = await service.get_fundamental_data(
            stock_code=stock_code,
            report_type=report_type,
            years=years
        )
        
        logger.info(f"返回股票 {stock_code} 的基本面数据")
        return fundamental_data
        
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"获取基本面数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取基本面数据失败")


@router.get("/market/overview")
async def get_market_overview(
    db: Session = Depends(get_db)
):
    """获取市场概览数据"""
    try:
        service = DataService(db)
        overview = await service.get_market_overview()
        
        logger.info("返回市场概览数据")
        return overview
        
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"获取市场概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取市场概览失败")


@router.get("/market/indices")
async def get_market_indices(
    db: Session = Depends(get_db)
):
    """获取市场指数数据"""
    try:
        service = DataService(db)
        indices = await service.get_market_indices()
        
        logger.info(f"返回 {len(indices)} 个市场指数")
        return indices
        
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"获取市场指数失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取市场指数失败")


@router.get("/flow/{stock_code}")
async def get_money_flow(
    stock_code: str,
    days: int = Query(5, ge=1, le=30, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取资金流向数据"""
    try:
        service = DataService(db)
        flow_data = await service.get_money_flow(
            stock_code=stock_code,
            days=days
        )
        
        logger.info(f"返回股票 {stock_code} 的资金流向数据")
        return flow_data
        
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"获取资金流向失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资金流向失败")


@router.post("/upload/csv")
async def upload_csv_data(
    file: UploadFile = File(...),
    data_type: str = Query(..., description="数据类型"),
    overwrite: bool = Query(False, description="是否覆盖现有数据"),
    db: Session = Depends(get_db)
):
    """上传CSV数据文件"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.csv'):
            raise ValidationException("只支持CSV文件")
        
        # 读取文件内容
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        service = DataService(db)
        result = await service.import_csv_data(
            data=df,
            data_type=data_type,
            overwrite=overwrite
        )
        
        logger.info(f"CSV数据上传成功: {result}")
        return {
            "message": "CSV数据上传成功",
            "filename": file.filename,
            "result": result
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CSV数据上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail="CSV数据上传失败")


@router.get("/export/csv")
async def export_csv_data(
    data_type: str = Query(..., description="数据类型"),
    stock_codes: Optional[List[str]] = Query(None, description="股票代码列表"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """导出CSV数据"""
    try:
        service = DataService(db)
        csv_data = await service.export_csv_data(
            data_type=data_type,
            stock_codes=stock_codes,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"CSV数据导出成功")
        
        # 返回CSV文件
        from fastapi.responses import StreamingResponse
        
        def generate():
            yield csv_data
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={data_type}_data.csv"}
        )
        
    except Exception as e:
        logger.error(f"CSV数据导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail="CSV数据导出失败")


@router.get("/cache/status")
async def get_cache_status(
    db: Session = Depends(get_db)
):
    """获取缓存状态"""
    try:
        service = DataService(db)
        cache_status = await service.get_cache_status()
        
        logger.info("返回缓存状态")
        return cache_status
        
    except Exception as e:
        logger.error(f"获取缓存状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取缓存状态失败")


@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = Query(None, description="缓存类型"),
    stock_codes: Optional[List[str]] = Query(None, description="股票代码列表"),
    db: Session = Depends(get_db)
):
    """清理缓存"""
    try:
        service = DataService(db)
        result = await service.clear_cache(
            cache_type=cache_type,
            stock_codes=stock_codes
        )
        
        logger.info(f"缓存清理完成: {result}")
        return {
            "message": "缓存清理成功",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"缓存清理失败: {str(e)}")
        raise HTTPException(status_code=500, detail="缓存清理失败")


@router.get("/quality/report")
async def get_data_quality_report(
    stock_codes: Optional[List[str]] = Query(None, description="股票代码列表"),
    days: int = Query(7, ge=1, le=30, description="检查天数"),
    db: Session = Depends(get_db)
):
    """获取数据质量报告"""
    try:
        service = DataService(db)
        quality_report = await service.get_data_quality_report(
            stock_codes=stock_codes,
            days=days
        )
        
        logger.info("返回数据质量报告")
        return quality_report
        
    except Exception as e:
        logger.error(f"获取数据质量报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据质量报告失败")