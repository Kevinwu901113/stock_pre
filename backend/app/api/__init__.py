#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由模块
"""

from fastapi import APIRouter
from .endpoints import data, recommend, strategy

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    data.router,
    prefix="/data",
    tags=["数据接口"]
)

api_router.include_router(
    recommend.router,
    prefix="/recommend",
    tags=["推荐接口"]
)

api_router.include_router(
    strategy.router,
    prefix="/strategy",
    tags=["策略接口"]
)