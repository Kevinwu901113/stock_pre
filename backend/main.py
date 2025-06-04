#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股量化推荐可视化系统 - 后端主入口
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import api_router
from app.core.logging import setup_logging

# 设置日志
setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="A股量化推荐系统API",
    description="提供股票推荐、数据查询和策略分析的API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """根路径健康检查"""
    return JSONResponse({
        "message": "A股量化推荐系统API",
        "version": "1.0.0",
        "status": "running"
    })


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    })


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )