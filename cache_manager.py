# -*- coding: utf-8 -*-
"""
缓存管理模块
功能：提供内存缓存和文件缓存功能
"""

import os
import pickle
import time
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "data_cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.memory_cache = {}
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        # 先检查内存缓存
        if key in self.memory_cache:
            data, expire_time = self.memory_cache[key]
            if expire_time is None or time.time() < expire_time:
                return data
            else:
                # 过期，删除
                del self.memory_cache[key]
        
        # 检查文件缓存
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data, expire_time = pickle.load(f)
                
                if expire_time is None or time.time() < expire_time:
                    # 加载到内存缓存
                    self.memory_cache[key] = (data, expire_time)
                    return data
                else:
                    # 过期，删除文件
                    os.remove(cache_file)
            except Exception as e:
                logger.warning(f"读取缓存文件失败: {e}")
                try:
                    os.remove(cache_file)
                except:
                    pass
        
        return None
    
    def set(self, key: str, data: Any, expire_minutes: Optional[int] = None):
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            expire_minutes: 过期时间（分钟），None表示永不过期
        """
        expire_time = None
        if expire_minutes is not None:
            expire_time = time.time() + expire_minutes * 60
        
        # 设置内存缓存
        self.memory_cache[key] = (data, expire_time)
        
        # 设置文件缓存
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump((data, expire_time), f)
        except Exception as e:
            logger.warning(f"写入缓存文件失败: {e}")
    
    def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key: 缓存键
        """
        # 删除内存缓存
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # 删除文件缓存
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception as e:
                logger.warning(f"删除缓存文件失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        # 清空内存缓存
        self.memory_cache.clear()
        
        # 清空文件缓存
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            logger.warning(f"清空缓存目录失败: {e}")
    
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        
        # 清理内存缓存
        expired_keys = []
        for key, (data, expire_time) in self.memory_cache.items():
            if expire_time is not None and current_time >= expire_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # 清理文件缓存
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'rb') as f:
                            data, expire_time = pickle.load(f)
                        
                        if expire_time is not None and current_time >= expire_time:
                            os.remove(cache_file)
                    except:
                        # 如果文件损坏，直接删除
                        try:
                            os.remove(cache_file)
                        except:
                            pass
        except Exception as e:
            logger.warning(f"清理过期缓存失败: {e}")