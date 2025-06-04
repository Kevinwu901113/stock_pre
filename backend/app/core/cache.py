#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存机制模块
提供统一的缓存接口，支持内存缓存和Redis缓存
"""

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from loguru import logger
from .config import settings
from .exceptions import CacheException


class CacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: str = "*") -> int:
        """清空缓存"""
        pass


class MemoryCache(CacheBackend):
    """内存缓存实现"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._expire_times: Dict[str, datetime] = {}
    
    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self._expire_times:
            return False
        return datetime.now() > self._expire_times[key]
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        expired_keys = []
        for key in self._expire_times:
            if self._is_expired(key):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._expire_times.pop(key, None)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            self._cleanup_expired()
            
            if key in self._cache and not self._is_expired(key):
                cache_data = self._cache[key]
                logger.debug(f"缓存命中: {key}")
                return cache_data.get("value")
            
            logger.debug(f"缓存未命中: {key}")
            return None
        except Exception as e:
            raise CacheException(f"获取缓存失败: {str(e)}", "GET", {"key": key})
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            self._cache[key] = {
                "value": value,
                "created_at": datetime.now()
            }
            
            if expire:
                self._expire_times[key] = datetime.now() + timedelta(seconds=expire)
            
            logger.debug(f"缓存设置成功: {key}, 过期时间: {expire}秒")
            return True
        except Exception as e:
            raise CacheException(f"设置缓存失败: {str(e)}", "SET", {"key": key})
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            deleted = key in self._cache
            self._cache.pop(key, None)
            self._expire_times.pop(key, None)
            
            if deleted:
                logger.debug(f"缓存删除成功: {key}")
            return deleted
        except Exception as e:
            raise CacheException(f"删除缓存失败: {str(e)}", "DELETE", {"key": key})
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        self._cleanup_expired()
        return key in self._cache and not self._is_expired(key)
    
    async def clear(self, pattern: str = "*") -> int:
        """清空缓存"""
        try:
            if pattern == "*":
                count = len(self._cache)
                self._cache.clear()
                self._expire_times.clear()
                logger.info(f"清空所有缓存，共 {count} 个")
                return count
            else:
                # 简单的模式匹配
                import fnmatch
                keys_to_delete = [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
                for key in keys_to_delete:
                    await self.delete(key)
                logger.info(f"清空匹配模式 {pattern} 的缓存，共 {len(keys_to_delete)} 个")
                return len(keys_to_delete)
        except Exception as e:
            raise CacheException(f"清空缓存失败: {str(e)}", "CLEAR", {"pattern": pattern})


class RedisCache(CacheBackend):
    """Redis缓存实现"""
    
    def __init__(self, redis_url: str):
        if not REDIS_AVAILABLE:
            raise CacheException("Redis不可用，请安装redis包", "INIT")
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Redis缓存初始化成功: {redis_url}")
        except Exception as e:
            raise CacheException(f"Redis连接失败: {str(e)}", "INIT", {"redis_url": redis_url})
    
    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """反序列化值"""
        return pickle.loads(value)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = self.redis_client.get(key)
            if value is not None:
                logger.debug(f"Redis缓存命中: {key}")
                return self._deserialize(value)
            
            logger.debug(f"Redis缓存未命中: {key}")
            return None
        except Exception as e:
            raise CacheException(f"Redis获取缓存失败: {str(e)}", "GET", {"key": key})
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            serialized_value = self._serialize(value)
            result = self.redis_client.set(key, serialized_value, ex=expire)
            
            if result:
                logger.debug(f"Redis缓存设置成功: {key}, 过期时间: {expire}秒")
            return bool(result)
        except Exception as e:
            raise CacheException(f"Redis设置缓存失败: {str(e)}", "SET", {"key": key})
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            result = self.redis_client.delete(key)
            if result:
                logger.debug(f"Redis缓存删除成功: {key}")
            return bool(result)
        except Exception as e:
            raise CacheException(f"Redis删除缓存失败: {str(e)}", "DELETE", {"key": key})
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            raise CacheException(f"Redis检查缓存存在性失败: {str(e)}", "EXISTS", {"key": key})
    
    async def clear(self, pattern: str = "*") -> int:
        """清空缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Redis清空匹配模式 {pattern} 的缓存，共 {count} 个")
                return count
            return 0
        except Exception as e:
            raise CacheException(f"Redis清空缓存失败: {str(e)}", "CLEAR", {"pattern": pattern})


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._backend: Optional[CacheBackend] = None
        self._initialize_backend()
    
    def _initialize_backend(self):
        """初始化缓存后端"""
        try:
            if settings.REDIS_ENABLED and REDIS_AVAILABLE:
                self._backend = RedisCache(settings.REDIS_URL)
                logger.info("使用Redis缓存后端")
            else:
                self._backend = MemoryCache()
                logger.info("使用内存缓存后端")
        except Exception as e:
            logger.warning(f"缓存后端初始化失败，使用内存缓存: {str(e)}")
            self._backend = MemoryCache()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return await self._backend.get(key)
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存"""
        if expire is None:
            expire = settings.CACHE_EXPIRE_MINUTES * 60
        return await self._backend.set(key, value, expire)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self._backend.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self._backend.exists(key)
    
    async def clear(self, pattern: str = "*") -> int:
        """清空缓存"""
        return await self._backend.clear(pattern)
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))
        
        # 添加关键字参数（按键排序确保一致性）
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)


# 全局缓存管理器实例
cache_manager = CacheManager()


# 缓存装饰器
def cached(prefix: str, expire: Optional[int] = None, key_func: Optional[callable] = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"使用缓存结果: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, expire)
            logger.debug(f"缓存函数结果: {cache_key}")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import asyncio
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # 根据函数类型返回对应的包装器
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 缓存预热功能
class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    async def warm_stock_data(self, stock_codes: list):
        """预热股票数据缓存"""
        logger.info(f"开始预热股票数据缓存，股票数量: {len(stock_codes)}")
        
        for code in stock_codes:
            try:
                # 这里可以调用数据服务预加载数据
                # 示例：await data_service.get_stock_data(code)
                logger.debug(f"预热股票数据: {code}")
            except Exception as e:
                logger.error(f"预热股票数据失败 {code}: {str(e)}")
        
        logger.info("股票数据缓存预热完成")
    
    async def warm_strategy_results(self):
        """预热策略结果缓存"""
        logger.info("开始预热策略结果缓存")
        
        try:
            # 这里可以调用策略服务预计算结果
            # 示例：await strategy_service.get_recommendations()
            logger.debug("预热策略结果")
        except Exception as e:
            logger.error(f"预热策略结果失败: {str(e)}")
        
        logger.info("策略结果缓存预热完成")


# 创建缓存预热器实例
cache_warmer = CacheWarmer(cache_manager)