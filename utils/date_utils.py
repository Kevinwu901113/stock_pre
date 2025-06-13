# -*- coding: utf-8 -*-
"""
日期工具模块，提供交易日判断、日期偏移等时间工具函数
"""

import datetime
import pandas as pd
import numpy as np
import os
import requests
import json
from functools import lru_cache

# 交易日历缓存文件路径
_CALENDAR_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache', 'trading_calendar.json')

@lru_cache(maxsize=1)
def _load_trading_calendar():
    """
    加载交易日历数据，优先从缓存文件加载，如果不存在则从网络获取
    
    Returns:
        list: 交易日列表，格式为YYYYMMDD的字符串
    """
    # 确保缓存目录存在
    cache_dir = os.path.dirname(_CALENDAR_CACHE_FILE)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # 尝试从缓存文件加载
    if os.path.exists(_CALENDAR_CACHE_FILE):
        try:
            with open(_CALENDAR_CACHE_FILE, 'r') as f:
                calendar_data = json.load(f)
                # 检查数据是否包含当前年份
                current_year = datetime.datetime.now().year
                if str(current_year) in calendar_data:
                    return calendar_data
        except Exception as e:
            print(f"Error loading trading calendar from cache: {e}")
    
    # 如果缓存不存在或无效，从网络获取
    try:
        # 获取从2000年至今的交易日历
        start_year = 2000
        end_year = datetime.datetime.now().year + 1
        calendar_data = {}
        
        for year in range(start_year, end_year + 1):
            # 这里使用tushare或其他数据源获取交易日历
            # 示例代码，实际使用时需要替换为真实的API调用
            # 以下是模拟数据，实际应用中应替换为真实API调用
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            
            # 模拟获取交易日历，实际应用中替换为API调用
            # 例如：calendar = tushare.trade_cal(start_date=start_date, end_date=end_date)
            # 这里使用pandas生成工作日作为模拟
            date_range = pd.date_range(start=start_date, end=end_date)
            # 过滤出工作日（周一至周五）
            trading_days = [d.strftime('%Y%m%d') for d in date_range if d.weekday() < 5]
            calendar_data[str(year)] = trading_days
        
        # 保存到缓存文件
        with open(_CALENDAR_CACHE_FILE, 'w') as f:
            json.dump(calendar_data, f)
        
        return calendar_data
    except Exception as e:
        print(f"Error fetching trading calendar: {e}")
        # 如果获取失败，返回空字典
        return {}

def _get_all_trading_days():
    """
    获取所有交易日列表
    
    Returns:
        list: 所有交易日列表，格式为YYYYMMDD的字符串
    """
    calendar_data = _load_trading_calendar()
    all_trading_days = []
    for year, days in calendar_data.items():
        all_trading_days.extend(days)
    return sorted(all_trading_days)

def is_trading_day(date=None):
    """
    判断给定日期是否为交易日
    
    Args:
        date (str or datetime, optional): 日期，格式为YYYYMMDD的字符串或datetime对象，默认为当天
        
    Returns:
        bool: 是否为交易日
    """
    if date is None:
        date = datetime.datetime.now()
    
    # 转换为YYYYMMDD格式的字符串
    if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
        date_str = date.strftime('%Y%m%d')
    else:
        date_str = str(date)
    
    # 获取交易日历
    calendar_data = _load_trading_calendar()
    year = date_str[:4]
    
    # 检查是否在交易日列表中
    if year in calendar_data:
        return date_str in calendar_data[year]
    return False

def get_previous_trading_day(date=None, n=1):
    """
    获取给定日期前n个交易日
    
    Args:
        date (str or datetime, optional): 日期，格式为YYYYMMDD的字符串或datetime对象，默认为当天
        n (int, optional): 前n个交易日，默认为1
        
    Returns:
        str: 前n个交易日，格式为YYYYMMDD的字符串
    """
    if date is None:
        date = datetime.datetime.now()
    
    # 转换为YYYYMMDD格式的字符串
    if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
        date_str = date.strftime('%Y%m%d')
    else:
        date_str = str(date)
    
    # 获取所有交易日
    all_trading_days = _get_all_trading_days()
    
    # 找到当前日期在交易日列表中的位置
    try:
        idx = all_trading_days.index(date_str)
        if idx >= n:
            return all_trading_days[idx - n]
        else:
            # 如果不足n个交易日，返回第一个交易日
            return all_trading_days[0]
    except ValueError:
        # 如果当前日期不是交易日，找到小于当前日期的最大交易日
        for day in sorted(all_trading_days, reverse=True):
            if day < date_str:
                return get_previous_trading_day(day, n - 1)
        # 如果没有找到，返回第一个交易日
        return all_trading_days[0]

def get_next_trading_day(date=None, n=1):
    """
    获取给定日期后n个交易日
    
    Args:
        date (str or datetime, optional): 日期，格式为YYYYMMDD的字符串或datetime对象，默认为当天
        n (int, optional): 后n个交易日，默认为1
        
    Returns:
        str: 后n个交易日，格式为YYYYMMDD的字符串
    """
    if date is None:
        date = datetime.datetime.now()
    
    # 转换为YYYYMMDD格式的字符串
    if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
        date_str = date.strftime('%Y%m%d')
    else:
        date_str = str(date)
    
    # 获取所有交易日
    all_trading_days = _get_all_trading_days()
    
    # 找到当前日期在交易日列表中的位置
    try:
        idx = all_trading_days.index(date_str)
        if idx + n < len(all_trading_days):
            return all_trading_days[idx + n]
        else:
            # 如果超出交易日列表范围，返回最后一个交易日
            return all_trading_days[-1]
    except ValueError:
        # 如果当前日期不是交易日，找到大于当前日期的最小交易日
        for day in sorted(all_trading_days):
            if day > date_str:
                return get_next_trading_day(day, n - 1)
        # 如果没有找到，返回最后一个交易日
        return all_trading_days[-1]

def get_trading_days_between(start_date, end_date):
    """
    获取两个日期之间的所有交易日
    
    Args:
        start_date (str or datetime): 开始日期，格式为YYYYMMDD的字符串或datetime对象
        end_date (str or datetime): 结束日期，格式为YYYYMMDD的字符串或datetime对象
        
    Returns:
        list: 交易日列表，格式为YYYYMMDD的字符串
    """
    # 转换为YYYYMMDD格式的字符串
    if isinstance(start_date, datetime.datetime) or isinstance(start_date, datetime.date):
        start_date_str = start_date.strftime('%Y%m%d')
    else:
        start_date_str = str(start_date)
    
    if isinstance(end_date, datetime.datetime) or isinstance(end_date, datetime.date):
        end_date_str = end_date.strftime('%Y%m%d')
    else:
        end_date_str = str(end_date)
    
    # 获取所有交易日
    all_trading_days = _get_all_trading_days()
    
    # 过滤出在范围内的交易日
    return [day for day in all_trading_days if start_date_str <= day <= end_date_str]

def get_trading_days_n_days_ago(n, end_date=None):
    """
    获取截止日期前n个交易日的列表
    
    Args:
        n (int): 交易日数量
        end_date (str or datetime, optional): 截止日期，格式为YYYYMMDD的字符串或datetime对象，默认为当天
        
    Returns:
        list: 交易日列表，格式为YYYYMMDD的字符串
    """
    if end_date is None:
        end_date = datetime.datetime.now()
    
    # 转换为YYYYMMDD格式的字符串
    if isinstance(end_date, datetime.datetime) or isinstance(end_date, datetime.date):
        end_date_str = end_date.strftime('%Y%m%d')
    else:
        end_date_str = str(end_date)
    
    # 获取所有交易日
    all_trading_days = _get_all_trading_days()
    
    # 找到截止日期在交易日列表中的位置
    try:
        idx = all_trading_days.index(end_date_str)
        if idx >= n - 1:
            return all_trading_days[idx - (n - 1):idx + 1]
        else:
            # 如果不足n个交易日，返回从第一个交易日到截止日期的所有交易日
            return all_trading_days[:idx + 1]
    except ValueError:
        # 如果截止日期不是交易日，找到小于截止日期的最大交易日
        for i, day in enumerate(sorted(all_trading_days, reverse=True)):
            if day < end_date_str:
                return get_trading_days_n_days_ago(n, day)
        # 如果没有找到，返回空列表
        return []

def get_trading_days_n_days_later(n, start_date=None):
    """
    获取起始日期后n个交易日的列表
    
    Args:
        n (int): 交易日数量
        start_date (str or datetime, optional): 起始日期，格式为YYYYMMDD的字符串或datetime对象，默认为当天
        
    Returns:
        list: 交易日列表，格式为YYYYMMDD的字符串
    """
    if start_date is None:
        start_date = datetime.datetime.now()
    
    # 转换为YYYYMMDD格式的字符串
    if isinstance(start_date, datetime.datetime) or isinstance(start_date, datetime.date):
        start_date_str = start_date.strftime('%Y%m%d')
    else:
        start_date_str = str(start_date)
    
    # 获取所有交易日
    all_trading_days = _get_all_trading_days()
    
    # 找到起始日期在交易日列表中的位置
    try:
        idx = all_trading_days.index(start_date_str)
        if idx + n <= len(all_trading_days):
            return all_trading_days[idx:idx + n]
        else:
            # 如果超出交易日列表范围，返回从起始日期到最后一个交易日的所有交易日
            return all_trading_days[idx:]
    except ValueError:
        # 如果起始日期不是交易日，找到大于起始日期的最小交易日
        for day in sorted(all_trading_days):
            if day > start_date_str:
                return get_trading_days_n_days_later(n, day)
        # 如果没有找到，返回空列表
        return []

def get_trade_dates(start_date, end_date):
    """
    获取指定日期范围内的交易日列表
    
    Args:
        start_date (str or datetime): 开始日期，格式为YYYYMMDD的字符串或datetime对象
        end_date (str or datetime): 结束日期，格式为YYYYMMDD的字符串或datetime对象
        
    Returns:
        list: 交易日列表，格式为YYYYMMDD的字符串
    """
    return get_trading_days_between(start_date, end_date)

def format_date(date, fmt='%Y%m%d'):
    """
    格式化日期
    
    Args:
        date (str or datetime): 日期，格式为YYYYMMDD的字符串或datetime对象
        fmt (str, optional): 输出格式，默认为'%Y%m%d'
        
    Returns:
        str: 格式化后的日期字符串
    """
    if isinstance(date, str):
        # 尝试解析字符串日期
        try:
            if len(date) == 8:  # YYYYMMDD格式
                date = datetime.datetime.strptime(date, '%Y%m%d')
            elif len(date) == 10 and '-' in date:  # YYYY-MM-DD格式
                date = datetime.datetime.strptime(date, '%Y-%m-%d')
            else:
                # 其他格式，尝试自动解析
                date = pd.to_datetime(date).to_pydatetime()
        except Exception as e:
            raise ValueError(f"无法解析日期字符串: {date}, 错误: {e}")
    
    # 格式化日期
    return date.strftime(fmt)

# 测试代码
if __name__ == '__main__':
    # 测试交易日判断
    print(f"今天是否为交易日: {is_trading_day()}")
    
    # 测试获取前一个交易日
    prev_day = get_previous_trading_day()
    print(f"前一个交易日: {prev_day}")
    
    # 测试获取后一个交易日
    next_day = get_next_trading_day()
    print(f"后一个交易日: {next_day}")
    
    # 测试获取两个日期之间的交易日
    start = '20230101'
    end = '20230131'
    trading_days = get_trading_days_between(start, end)
    print(f"2023年1月的交易日数量: {len(trading_days)}")
    
    # 测试日期格式化
    date_str = '20230101'
    formatted = format_date(date_str, '%Y-%m-%d')
    print(f"格式化日期: {formatted}")