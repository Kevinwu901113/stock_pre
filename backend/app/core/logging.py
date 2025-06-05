import os
import sys
from loguru import logger
from datetime import datetime
from config.settings import settings

def setup_logging():
    """设置日志配置"""
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # 确保日志目录存在
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # 应用日志文件
    logger.add(
        os.path.join(settings.LOG_DIR, "app.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # 推荐生成专用日志
    logger.add(
        os.path.join(settings.LOG_DIR, "recommendations.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        rotation="1 day",
        retention="90 days",
        filter=lambda record: "recommendation" in record["name"].lower()
    )
    
    # 错误日志文件
    logger.add(
        os.path.join(settings.LOG_DIR, "errors.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation="1 week",
        retention="12 weeks"
    )
    
    # API访问日志
    logger.add(
        os.path.join(settings.LOG_DIR, "api_access.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        filter=lambda record: "api_access" in record["extra"].get("category", "")
    )
    
    return logger

class RecommendationLogger:
    """推荐生成专用日志记录器"""
    
    def __init__(self):
        self.logger = logger.bind(name="recommendation")
    
    def log_generation_start(self, task_id: str, stock_codes: list, strategies: list):
        """记录推荐生成开始"""
        self.logger.info(
            f"推荐生成开始 - 任务ID: {task_id} | "
            f"股票数量: {len(stock_codes)} | "
            f"股票代码: {', '.join(stock_codes[:5])}{'...' if len(stock_codes) > 5 else ''} | "
            f"策略: {', '.join(strategies)} | "
            f"开始时间: {datetime.now()}"
        )
    
    def log_generation_complete(self, task_id: str, recommendations_count: int, duration: float):
        """记录推荐生成完成"""
        self.logger.info(
            f"推荐生成完成 - 任务ID: {task_id} | "
            f"生成数量: {recommendations_count} | "
            f"耗时: {duration:.2f}秒 | "
            f"完成时间: {datetime.now()}"
        )
    
    def log_generation_error(self, task_id: str, error: str):
        """记录推荐生成错误"""
        self.logger.error(
            f"推荐生成失败 - 任务ID: {task_id} | "
            f"错误信息: {error} | "
            f"失败时间: {datetime.now()}"
        )
    
    def log_strategy_execution(self, strategy_name: str, stock_code: str, result: dict):
        """记录策略执行结果"""
        self.logger.info(
            f"策略执行 - 策略: {strategy_name} | "
            f"股票: {stock_code} | "
            f"信号: {result.get('signal', 'none')} | "
            f"置信度: {result.get('confidence', 0):.3f} | "
            f"目标价: {result.get('target_price', 'N/A')} | "
            f"止损价: {result.get('stop_loss', 'N/A')}"
        )
    
    def log_data_sync(self, source: str, stock_count: int, success: bool, duration: float):
        """记录数据同步"""
        status = "成功" if success else "失败"
        self.logger.info(
            f"数据同步{status} - 数据源: {source} | "
            f"股票数量: {stock_count} | "
            f"耗时: {duration:.2f}秒 | "
            f"时间: {datetime.now()}"
        )
    
    def log_model_prediction(self, model_name: str, stock_code: str, prediction: dict):
        """记录模型预测"""
        self.logger.info(
            f"模型预测 - 模型: {model_name} | "
            f"股票: {stock_code} | "
            f"预测结果: {prediction.get('prediction', 'N/A')} | "
            f"概率: {prediction.get('probability', 0):.3f}"
        )

class APIAccessLogger:
    """API访问日志记录器"""
    
    def __init__(self):
        self.logger = logger.bind(category="api_access")
    
    def log_request(self, request_id: str, method: str, url: str, client_ip: str, user_agent: str = None):
        """记录API请求"""
        self.logger.info(
            f"API请求 - ID: {request_id} | "
            f"方法: {method} | "
            f"URL: {url} | "
            f"客户端IP: {client_ip} | "
            f"User-Agent: {user_agent or 'Unknown'}",
            extra={"category": "api_access"}
        )
    
    def log_response(self, request_id: str, status_code: int, duration: float, response_size: int = None):
        """记录API响应"""
        self.logger.info(
            f"API响应 - ID: {request_id} | "
            f"状态码: {status_code} | "
            f"耗时: {duration:.3f}秒 | "
            f"响应大小: {response_size or 'Unknown'} bytes",
            extra={"category": "api_access"}
        )
    
    def log_error(self, request_id: str, error_type: str, error_message: str):
        """记录API错误"""
        self.logger.error(
            f"API错误 - ID: {request_id} | "
            f"错误类型: {error_type} | "
            f"错误信息: {error_message}",
            extra={"category": "api_access"}
        )

class PerformanceLogger:
    """性能监控日志记录器"""
    
    def __init__(self):
        self.logger = logger.bind(name="performance")
    
    def log_database_query(self, query_type: str, table: str, duration: float, record_count: int = None):
        """记录数据库查询性能"""
        self.logger.info(
            f"数据库查询 - 类型: {query_type} | "
            f"表: {table} | "
            f"耗时: {duration:.3f}秒 | "
            f"记录数: {record_count or 'N/A'}"
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, duration: float = None):
        """记录缓存操作"""
        hit_status = f" | 命中: {'是' if hit else '否'}" if hit is not None else ""
        duration_info = f" | 耗时: {duration:.3f}秒" if duration is not None else ""
        
        self.logger.info(
            f"缓存操作 - 操作: {operation} | "
            f"键: {key}{hit_status}{duration_info}"
        )
    
    def log_memory_usage(self, process_memory: float, system_memory: float):
        """记录内存使用情况"""
        self.logger.info(
            f"内存使用 - 进程内存: {process_memory:.2f}MB | "
            f"系统内存: {system_memory:.2f}%"
        )

# 全局日志记录器实例
recommendation_logger = RecommendationLogger()
api_access_logger = APIAccessLogger()
performance_logger = PerformanceLogger()

# 初始化日志系统
setup_logging()