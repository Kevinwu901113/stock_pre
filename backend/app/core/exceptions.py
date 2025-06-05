from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback
from typing import Union


class StockAPIException(Exception):
    """自定义API异常基类"""
    
    def __init__(self, message: str, code: int = 500, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DataSourceException(StockAPIException):
    """数据源异常"""
    
    def __init__(self, message: str, source: str = None, details: dict = None):
        super().__init__(message, 503, details)
        self.source = source


class StrategyException(StockAPIException):
    """策略异常"""
    
    def __init__(self, message: str, strategy: str = None, details: dict = None):
        super().__init__(message, 422, details)
        self.strategy = strategy


class CacheException(StockAPIException):
    """缓存异常"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 503, details)


class ValidationException(StockAPIException):
    """验证异常"""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, 400, details)
        self.field = field


def create_error_response(
    message: str,
    code: int = 500,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """创建错误响应（兼容旧版本）"""
    from datetime import datetime
    from backend.app.core.response import error_response
    
    # 使用新的统一响应格式
    return error_response(
        message=message,
        code=code,
        data=details,
        request_id=request_id
    )


async def stock_api_exception_handler(request: Request, exc: StockAPIException):
    """自定义API异常处理器"""
    logger.error(f"StockAPIException: {exc.message} - Details: {exc.details}")
    
    return create_error_response(
        message=exc.message,
        code=exc.code,
        details=exc.details
    )


async def data_source_exception_handler(request: Request, exc: DataSourceException):
    """数据源异常处理器"""
    logger.error(f"DataSourceException from {exc.source}: {exc.message}")
    
    details = exc.details.copy() if exc.details else {}
    if exc.source:
        details["source"] = exc.source
    
    return create_error_response(
        message=f"数据源错误: {exc.message}",
        code=exc.code,
        details=details
    )


async def strategy_exception_handler(request: Request, exc: StrategyException):
    """策略异常处理器"""
    logger.error(f"StrategyException in {exc.strategy}: {exc.message}")
    
    details = exc.details.copy() if exc.details else {}
    if exc.strategy:
        details["strategy"] = exc.strategy
    
    return create_error_response(
        message=f"策略错误: {exc.message}",
        code=exc.code,
        details=details
    )


async def validation_exception_handler(request: Request, exc: ValidationException):
    """验证异常处理器"""
    logger.warning(f"ValidationException: {exc.message} - Field: {exc.field}")
    
    details = exc.details.copy() if exc.details else {}
    if exc.field:
        details["field"] = exc.field
    
    return create_error_response(
        message=f"参数验证错误: {exc.message}",
        code=exc.code,
        details=details
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]):
    """HTTP异常处理器"""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    return create_error_response(
        message=str(exc.detail),
        code=exc.status_code
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """请求验证错误处理器"""
    logger.warning(f"RequestValidationError: {exc.errors()}")
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        message="请求参数验证失败",
        code=422,
        details={"validation_errors": errors}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # 生产环境不暴露详细错误信息
    from config.settings import settings
    
    if settings.DEBUG:
        details = {
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    else:
        details = None
    
    return create_error_response(
        message="服务器内部错误",
        code=500,
        details=details
    )


def setup_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    
    # 自定义异常处理器
    app.add_exception_handler(StockAPIException, stock_api_exception_handler)
    app.add_exception_handler(DataSourceException, data_source_exception_handler)
    app.add_exception_handler(StrategyException, strategy_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    
    # 标准异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    
    # 通用异常处理器(最后添加)
    app.add_exception_handler(Exception, general_exception_handler)