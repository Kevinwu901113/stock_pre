"""API模块"""

# 导入所有API路由
from . import recommendations, stocks, strategies, data

__all__ = [
    "recommendations",
    "stocks", 
    "strategies",
    "data"
]