from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from .settings import settings


# SQLAlchemy配置
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False
    } if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata = MetaData()


# Redis配置 (可选)
redis_client = None
if settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # 测试连接
        redis_client.ping()
    except Exception as e:
        print(f"Redis连接失败: {e}")
        redis_client = None


# 数据库依赖
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis依赖
def get_redis():
    """获取Redis客户端"""
    return redis_client


# 数据库初始化
def init_database():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


# 缓存工具函数
class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis()
    
    def get(self, key: str):
        """获取缓存"""
        if not self.redis:
            return None
        try:
            return self.redis.get(key)
        except Exception as e:
            print(f"缓存获取失败: {e}")
            return None
    
    def set(self, key: str, value: str, expire: int = None):
        """设置缓存"""
        if not self.redis:
            return False
        try:
            if expire:
                return self.redis.setex(key, expire, value)
            else:
                return self.redis.set(key, value)
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False
    
    def delete(self, key: str):
        """删除缓存"""
        if not self.redis:
            return False
        try:
            return self.redis.delete(key)
        except Exception as e:
            print(f"缓存删除失败: {e}")
            return False
    
    def exists(self, key: str):
        """检查缓存是否存在"""
        if not self.redis:
            return False
        try:
            return self.redis.exists(key)
        except Exception as e:
            print(f"缓存检查失败: {e}")
            return False
    
    def flush_all(self):
        """清空所有缓存"""
        if not self.redis:
            return False
        try:
            return self.redis.flushall()
        except Exception as e:
            print(f"缓存清空失败: {e}")
            return False


# 创建全局缓存管理器实例
cache_manager = CacheManager()