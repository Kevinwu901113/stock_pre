# -*- coding: utf-8 -*-
"""
日志模块，提供统一的日志打印和保存接口
"""

import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import datetime

# 全局日志字典，用于存储不同名称的日志实例
_loggers = {}

def setup_logger(name, log_file=None, level=logging.INFO, console_output=True, 
               max_bytes=10*1024*1024, backup_count=5, when='midnight'):
    """
    设置日志记录器
    
    Args:
        name (str): 日志记录器名称
        log_file (str, optional): 日志文件路径，如果为None则不保存到文件
        level (int, optional): 日志级别，默认为INFO
        console_output (bool, optional): 是否输出到控制台，默认为True
        max_bytes (int, optional): 单个日志文件最大字节数，默认为10MB
        backup_count (int, optional): 备份文件数量，默认为5
        when (str, optional): 时间轮转方式，默认为'midnight'，每天午夜轮转
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    # 如果已经存在同名logger，直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # 避免日志传递到父logger
    
    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 根据文件名判断使用哪种文件处理器
        if max_bytes > 0:
            # 使用大小轮转的文件处理器
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
        else:
            # 使用时间轮转的文件处理器
            file_handler = TimedRotatingFileHandler(
                log_file, when=when, backupCount=backup_count, encoding='utf-8'
            )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 保存到全局字典
    _loggers[name] = logger
    
    return logger

def get_logger(name):
    """
    获取已创建的日志记录器，如果不存在则创建一个默认的
    
    Args:
        name (str): 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    if name not in _loggers:
        # 如果不存在，创建一个默认的日志记录器
        today = datetime.datetime.now().strftime('%Y%m%d')
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f'{name}_{today}.log')
        return setup_logger(name, log_file)
    
    return _loggers[name]

# 创建默认的应用日志记录器
def _create_default_logger():
    """
    创建默认的应用日志记录器
    """
    today = datetime.datetime.now().strftime('%Y%m%d')
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, f'app_{today}.log')
    return setup_logger('app', log_file)

# 默认应用日志记录器
app_logger = _create_default_logger()

# 测试代码
if __name__ == '__main__':
    # 测试日志功能
    logger = get_logger('test')
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')