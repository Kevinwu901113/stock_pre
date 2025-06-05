from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
import uuid
from typing import Callable


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"Request started - ID: {request_id} | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录响应信息
        logger.info(
            f"Request completed - ID: {request_id} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 允许的调用次数
        self.period = period  # 时间窗口(秒)
        self.clients = {}  # 客户端请求记录
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.clients:
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if current_time - timestamp < self.period
            ]
        else:
            self.clients[client_ip] = []
        
        # 检查速率限制
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(f"Rate limit exceeded for client: {client_ip}")
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.period))
                }
            )
        
        # 记录请求时间
        self.clients[client_ip].append(current_time)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头
        remaining = self.calls - len(self.clients[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""
    
    def __init__(self, app, cache_paths: dict = None):
        super().__init__(app)
        # 默认缓存配置
        self.cache_paths = cache_paths or {
            "/api/v1/stocks": "public, max-age=300",  # 5分钟
            "/api/v1/data": "public, max-age=600",    # 10分钟
            "/health": "public, max-age=60",          # 1分钟
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 根据路径设置缓存头
        path = request.url.path
        for cache_path, cache_control in self.cache_paths.items():
            if path.startswith(cache_path):
                response.headers["Cache-Control"] = cache_control
                break
        else:
            # 默认不缓存
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Middleware caught exception: {str(e)}")
            # 这里可以添加额外的错误处理逻辑
            # 比如发送错误通知、记录错误统计等
            raise  # 重新抛出异常，让异常处理器处理


def setup_middleware(app: FastAPI):
    """设置中间件"""
    
    # 错误处理中间件(最先添加，最后执行)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 缓存控制中间件
    app.add_middleware(CacheControlMiddleware)
    
    # 速率限制中间件
    app.add_middleware(RateLimitMiddleware, calls=1000, period=60)
    
    # 请求日志中间件(最后添加，最先执行)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("中间件设置完成")