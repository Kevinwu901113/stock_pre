#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块
提供统一的异常定义和处理机制
"""

import traceback
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger


class BaseStockException(Exception):
    """基础股票系统异常类"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DataSourceException(BaseStockException):
    """数据源异常"""
    
    def __init__(self, message: str, source: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"DATA_SOURCE_ERROR_{source.upper()}", details)
        self.source = source


class StrategyException(BaseStockException):
    """策略执行异常"""
    
    def __init__(self, message: str, strategy_name: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"STRATEGY_ERROR_{strategy_name.upper()}", details)
        self.strategy_name = strategy_name


class CacheException(BaseStockException):
    """缓存异常"""
    
    def __init__(self, message: str, operation: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"CACHE_ERROR_{operation.upper()}", details)
        self.operation = operation


class ValidationException(BaseStockException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"VALIDATION_ERROR_{field.upper()}", details)
        self.field = field


class ExternalAPIException(BaseStockException):
    """外部API调用异常"""
    
    def __init__(self, message: str, api_name: str = "unknown", status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"EXTERNAL_API_ERROR_{api_name.upper()}", details)
        self.api_name = api_name
        self.status_code = status_code


class ExceptionHandler:
    """统一异常处理器"""
    
    @staticmethod
    def log_exception(exc: Exception, context: str = "", extra_info: Optional[Dict[str, Any]] = None):
        """记录异常日志"""
        error_info = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        if extra_info:
            error_info.update(extra_info)
            
        if isinstance(exc, BaseStockException):
            error_info.update({
                "error_code": exc.code,
                "error_details": exc.details
            })
            
        logger.error(f"异常发生: {context}", **error_info)
    
    @staticmethod
    def create_error_response(exc: Exception, status_code: int = 500) -> Dict[str, Any]:
        """创建标准化错误响应"""
        if isinstance(exc, BaseStockException):
            return {
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                },
                "data": None
            }
        else:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "服务器内部错误",
                    "details": {"original_error": str(exc)}
                },
                "data": None
            }


# FastAPI异常处理器
async def stock_exception_handler(request: Request, exc: BaseStockException):
    """处理自定义股票系统异常"""
    ExceptionHandler.log_exception(exc, f"API请求: {request.url}")
    
    status_code = 400
    if isinstance(exc, DataSourceException):
        status_code = 503  # Service Unavailable
    elif isinstance(exc, ValidationException):
        status_code = 422  # Unprocessable Entity
    elif isinstance(exc, ExternalAPIException):
        status_code = 502  # Bad Gateway
    
    return JSONResponse(
        status_code=status_code,
        content=ExceptionHandler.create_error_response(exc, status_code)
    )


async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    ExceptionHandler.log_exception(exc, f"API请求: {request.url}")
    
    return JSONResponse(
        status_code=500,
        content=ExceptionHandler.create_error_response(exc, 500)
    )


# 装饰器：异常捕获和处理
def handle_exceptions(context: str = ""):
    """异常处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseStockException as e:
                ExceptionHandler.log_exception(e, context or func.__name__)
                raise
            except Exception as e:
                ExceptionHandler.log_exception(e, context or func.__name__)
                raise BaseStockException(
                    message=f"执行 {func.__name__} 时发生未知错误: {str(e)}",
                    code="UNKNOWN_ERROR",
                    details={"function": func.__name__, "original_error": str(e)}
                )
        return wrapper
    return decorator


# 异步版本的装饰器
def handle_async_exceptions(context: str = ""):
    """异步异常处理装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseStockException as e:
                ExceptionHandler.log_exception(e, context or func.__name__)
                raise
            except Exception as e:
                ExceptionHandler.log_exception(e, context or func.__name__)
                raise BaseStockException(
                    message=f"执行 {func.__name__} 时发生未知错误: {str(e)}",
                    code="UNKNOWN_ERROR",
                    details={"function": func.__name__, "original_error": str(e)}
                )
        return wrapper
    return decorator