from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "A股量化选股推荐系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:////home/wjk/workplace/stock/data/stock.db"
    
    # Redis配置 (可选)
    REDIS_URL: Optional[str] = None
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ]
    
    # 数据源配置
    TUSHARE_TOKEN: Optional[str] = None
    SINA_API_ENABLED: bool = True
    EASTMONEY_API_ENABLED: bool = True
    
    # 数据缓存配置
    CACHE_EXPIRE_MINUTES: int = 30
    DATA_SYNC_INTERVAL_MINUTES: int = 60
    
    # 策略配置
    DEFAULT_STRATEGIES: List[str] = [
        "technical.ma_strategy",
        "technical.rsi_strategy",
        "fundamental.pe_strategy"
    ]
    
    # 推荐配置
    MAX_BUY_RECOMMENDATIONS: int = 10
    MAX_SELL_RECOMMENDATIONS: int = 10
    MIN_CONFIDENCE_SCORE: float = 0.6
    
    # 数据目录
    DATA_DIR: str = "./data"
    LOG_DIR: str = "./logs"
    CSV_DATA_DIR: str = "./data/csv"  # CSV数据源目录
    CACHE_DIR: str = "./data/cache"  # 缓存目录
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # AI模型配置(预留)
    AI_MODEL_ENABLED: bool = False
    AI_MODEL_PATH: str = "./ai/models"
    
    # AI模型配置
    AI_ENABLED: bool = True
    AI_MODEL_PATHS: dict = {
        'recommendation': 'models/recommendation',
        'strategy': 'models/strategy',
        'nlp': 'models/nlp',
        'general': 'models/general'
    }
    
    AI_MODEL_CONFIGS: dict = {
        'preload_models': ['recommendation_model'],  # 预加载的模型
        'model_timeout': 30,  # 模型加载超时时间（秒）
        'max_models': 5,  # 最大同时加载的模型数量
        'auto_unload': True,  # 是否自动卸载未使用的模型
        'unload_threshold': 3600  # 自动卸载阈值（秒）
    }
    
    # 市场配置
    MARKET_OPEN_TIME: str = "09:30"
    MARKET_CLOSE_TIME: str = "15:00"
    TRADING_DAYS_ONLY: bool = True
    
    # 风险控制
    MAX_POSITION_SIZE: float = 0.1  # 单只股票最大仓位
    STOP_LOSS_RATIO: float = 0.05   # 止损比例
    TAKE_PROFIT_RATIO: float = 0.15  # 止盈比例
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 数据源配置
DATA_SOURCES = {
    "tushare": {
        "enabled": bool(settings.TUSHARE_TOKEN),
        "token": settings.TUSHARE_TOKEN,
        "rate_limit": 200,  # 每分钟请求限制
        "priority": 1
    },
    "sina": {
        "enabled": settings.SINA_API_ENABLED,
        "base_url": "https://hq.sinajs.cn",
        "rate_limit": 1000,
        "priority": 2
    },
    "eastmoney": {
        "enabled": settings.EASTMONEY_API_ENABLED,
        "base_url": "https://push2.eastmoney.com",
        "rate_limit": 500,
        "priority": 3
    },
    "csv": {
        "enabled": True,
        "data_dir": settings.CSV_DATA_DIR,
        "priority": 99  # 最低优先级，作为备用
    }
}


# 策略配置
STRATEGY_CONFIG = {
    "technical": {
        "ma_strategy": {
            "enabled": True,
            "weight": 0.3,
            "params": {
                "short_period": 5,
                "long_period": 20
            }
        },
        "rsi_strategy": {
            "enabled": True,
            "weight": 0.2,
            "params": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        },
        "macd_strategy": {
            "enabled": True,
            "weight": 0.2,
            "params": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        }
    },
    "fundamental": {
        "pe_strategy": {
            "enabled": True,
            "weight": 0.2,
            "params": {
                "max_pe": 30,
                "min_pe": 5
            }
        },
        "pb_strategy": {
            "enabled": True,
            "weight": 0.1,
            "params": {
                "max_pb": 3,
                "min_pb": 0.5
            }
        }
    },
    "sentiment": {
        "volume_strategy": {
            "enabled": False,
            "weight": 0.1,
            "params": {
                "volume_ratio_threshold": 2.0
            }
        }
    }
}