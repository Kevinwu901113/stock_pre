"""数据缓存模块

提供Redis缓存功能，支持数据的存储、获取和过期管理。
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from loguru import logger

from config.settings import settings


class DataCache:
    """数据缓存类
    
    使用Redis作为缓存后端，支持JSON和二进制数据存储。
    """
    
    def __init__(self):
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False  # 支持二进制数据
            )
            logger.info("Redis缓存初始化成功")
        except Exception as e:
            logger.error(f"Redis缓存初始化失败: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在返回None
        """
        if not self.redis_client:
            return None
            
        try:
            # 添加前缀
            cache_key = f"stock_data:{key}"
            
            # 获取数据
            data = await self.redis_client.get(cache_key)
            if data is None:
                return None
            
            # 尝试JSON解析
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 如果JSON解析失败，尝试pickle反序列化
                try:
                    return pickle.loads(data)
                except Exception:
                    logger.warning(f"缓存数据反序列化失败: {cache_key}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """设置缓存数据
        
        Args:
            key: 缓存键
            value: 要缓存的数据
            expire: 过期时间（秒），None表示不过期
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
            
        try:
            # 添加前缀
            cache_key = f"stock_data:{key}"
            
            # 序列化数据
            try:
                # 优先使用JSON序列化
                serialized_data = json.dumps(value, ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                # JSON序列化失败时使用pickle
                serialized_data = pickle.dumps(value)
            
            # 设置缓存
            if expire:
                await self.redis_client.setex(cache_key, expire, serialized_data)
            else:
                await self.redis_client.set(cache_key, serialized_data)
                
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.redis_client:
            return False
            
        try:
            cache_key = f"stock_data:{key}"
            result = await self.redis_client.delete(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            缓存是否存在
        """
        if not self.redis_client:
            return False
            
        try:
            cache_key = f"stock_data:{key}"
            result = await self.redis_client.exists(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
            
        try:
            cache_key = f"stock_data:{key}"
            result = await self.redis_client.expire(cache_key, seconds)
            return result
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取缓存剩余生存时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余生存时间（秒），-1表示永不过期，-2表示不存在
        """
        if not self.redis_client:
            return -2
            
        try:
            cache_key = f"stock_data:{key}"
            return await self.redis_client.ttl(cache_key)
        except Exception as e:
            logger.error(f"获取缓存TTL失败 {key}: {e}")
            return -2
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存
        
        Args:
            pattern: 匹配模式，支持通配符
            
        Returns:
            删除的缓存数量
        """
        if not self.redis_client:
            return 0
            
        try:
            cache_pattern = f"stock_data:{pattern}"
            keys = await self.redis_client.keys(cache_pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"清除缓存模式失败 {pattern}: {e}")
            return 0
    
    async def get_cache_info(self) -> dict:
        """获取缓存信息
        
        Returns:
            缓存统计信息
        """
        if not self.redis_client:
            return {'status': 'disconnected'}
            
        try:
            info = await self.redis_client.info()
            
            # 获取股票数据相关的键数量
            keys = await self.redis_client.keys("stock_data:*")
            
            return {
                'status': 'connected',
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'stock_data_keys': len(keys),
                'uptime_in_seconds': info.get('uptime_in_seconds')
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            缓存是否健康
        """
        if not self.redis_client:
            return False
            
        try:
            # 执行ping命令
            pong = await self.redis_client.ping()
            return pong
        except Exception as e:
            logger.error(f"缓存健康检查失败: {e}")
            return False
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis连接已关闭")


# 缓存装饰器
def cache_result(expire: int = 3600, key_prefix: str = ""):
    """缓存结果装饰器
    
    Args:
        expire: 过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cache = DataCache()
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await cache.set(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator