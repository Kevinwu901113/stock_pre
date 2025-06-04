#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
"""

import os
import sys
from loguru import logger
from .config import settings


def setup_logging():
    """设置日志配置"""
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    # 添加控制台日志处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 添加文件日志处理器
    logger.add(
        settings.LOG_FILE,
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    error_log_file = settings.LOG_FILE.replace(".log", "_error.log")
    logger.add(
        error_log_file,
        format=file_format,
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成，日志级别: {settings.LOG_LEVEL}")


# 获取日志记录器
def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger