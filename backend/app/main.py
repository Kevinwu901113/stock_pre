from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.settings import settings
from config.database import init_database
from backend.app.api import recommendations, stocks, strategies, data, stats, recommendation_generator
from backend.app.api import stocks_search, stocks_kline, stocks_indicators
from backend.app.core.exceptions import setup_exception_handlers
from backend.app.core.middleware import setup_middleware
from loguru import logger


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A股量化选股推荐系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置受信任主机
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 生产环境应该限制具体域名
)

# 设置自定义中间件
setup_middleware(app)

# 设置异常处理器
setup_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    try:
        init_database()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    
    # 启动定时任务调度器
    try:
        from backend.app.core.scheduler import start_scheduler
        await start_scheduler()
        logger.info("定时任务调度器启动成功")
    except Exception as e:
        logger.error(f"定时任务调度器启动失败: {e}")
    
    # 其他启动任务
    logger.info("应用启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用正在关闭...")
    
    # 停止定时任务调度器
    try:
        from backend.app.core.scheduler import stop_scheduler
        await stop_scheduler()
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止定时任务调度器失败: {e}")
    
    logger.info("应用关闭完成")


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用{settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# 注册API路由
app.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["推荐"]
)

app.include_router(
    recommendation_generator.router,
    prefix="/recommendations",
    tags=["推荐生成"]
)

app.include_router(
    stocks.router,
    prefix="/stocks",
    tags=["股票"]
)

# 注册股票搜索路由
app.include_router(
    stocks_search.router,
    prefix="/stocks",
    tags=["股票搜索"]
)

# 注册股票K线路由
app.include_router(
    stocks_kline.router,
    prefix="/stocks",
    tags=["股票K线"]
)

# 注册股票技术指标路由
app.include_router(
    stocks_indicators.router,
    prefix="/stocks",
    tags=["股票技术指标"]
)

app.include_router(
    strategies.router,
    prefix="/strategies",
    tags=["策略"]
)

app.include_router(
    data.router,
    prefix="/data",
    tags=["数据"]
)

app.include_router(
    stats.router,
    prefix="/stats",
    tags=["统计"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )