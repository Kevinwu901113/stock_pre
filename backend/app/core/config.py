#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置模块
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "A股量化推荐系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="ALLOWED_HOSTS"
    )
    
    # 数据源配置
    TUSHARE_TOKEN: str = Field(default="", env="TUSHARE_TOKEN")
    AKSHARE_ENABLED: bool = Field(default=True, env="AKSHARE_ENABLED")
    
    # 数据库配置（可选）
    DATABASE_URL: str = Field(default="sqlite:///./stock_data.db", env="DATABASE_URL")
    
    # Redis配置（可选）
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    
    # 缓存配置
    CACHE_EXPIRE_MINUTES: int = Field(default=30, env="CACHE_EXPIRE_MINUTES")
    
    # 数据目录
    DATA_DIR: str = Field(default="../data", env="DATA_DIR")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # 策略配置
    STRATEGY_CONFIG: dict = {
        "evening_buy": {
            "enabled": True,
            "run_time": "14:50",  # 尾盘运行时间
            "params": {
                "ma_period": 5,
                "volume_threshold": 1.5,
                "min_market_cap": 50  # 最小市值（亿）
            }
        },
        "morning_sell": {
            "enabled": True,
            "run_time": "09:35",  # 早盘运行时间
            "params": {
                "profit_threshold": 0.05,  # 止盈阈值
                "loss_threshold": -0.03   # 止损阈值
            }
        }
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()