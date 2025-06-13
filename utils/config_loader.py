# -*- coding: utf-8 -*-
"""
配置加载模块，解析并校验配置文件，供主流程调用
"""

import os
import yaml
import json
import jsonschema
from typing import Dict, Any, Optional
from .logger import get_logger

# 获取日志记录器
logger = get_logger('config_loader')

# 全局配置字典
_config = {}

# 配置文件路径
_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

# 配置文件模式定义
_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["data_source", "features", "model", "backtest", "strategy"],
    "properties": {
        "data_source": {
            "type": "object",
            "required": ["type", "start_date", "end_date"],
            "properties": {
                "type": {"type": "string", "enum": ["akshare", "local"]},
                "provider": {"type": "string"},
                "api_key": {"type": "string"},
                "api_url": {"type": "string"},
                "start_date": {"type": "string", "pattern": "^\\d{8}$"},
                "end_date": {"type": "string", "pattern": "^\\d{8}$"},
                "stock_pool": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "index_pool": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "cache_dir": {"type": "string"},
                "akshare": {
                    "type": "object",
                    "properties": {
                        "adjust": {"type": "string", "enum": ["qfq", "hfq", "none"]},
                        "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                        "request_delay": {"type": "number", "minimum": 0},
                        "retry_times": {"type": "integer", "minimum": 1},
                        "retry_delay": {"type": "number", "minimum": 0}
                    }
                }
            }
        },
        "features": {
            "type": "object",
            "properties": {
                "technical_indicators": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "fundamental_indicators": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "selection_method": {"type": "string", "enum": ["correlation", "mutual_info", "rfe", "lasso"]},
                "top_n_features": {"type": "integer", "minimum": 1}
            }
        },
        "model": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["xgboost", "lightgbm", "catboost", "lstm", "ensemble"]},
                "params": {"type": "object"},
                "train_test_split": {"type": "number", "minimum": 0.1, "maximum": 0.9},
                "cv_folds": {"type": "integer", "minimum": 2},
                "target_variable": {"type": "string"},
                "model_save_path": {"type": "string"}
            }
        },
        "llm": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "model_name": {"type": "string"},
                "news_sources": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "max_tokens": {"type": "integer", "minimum": 1},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "cache_dir": {"type": "string"}
            }
        },
        "backtest": {
            "type": "object",
            "properties": {
                "initial_capital": {"type": "number", "minimum": 0},
                "commission_rate": {"type": "number", "minimum": 0},
                "slippage": {"type": "number", "minimum": 0},
                "benchmark": {"type": "string"},
                "rebalance_frequency": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                "risk_free_rate": {"type": "number", "minimum": 0}
            }
        },
        "strategy": {
            "type": "object",
            "properties": {
                "max_positions": {"type": "integer", "minimum": 1},
                "position_sizing": {"type": "string", "enum": ["equal", "market_cap", "volatility", "score"]},
                "stop_loss": {"type": "number", "minimum": 0},
                "take_profit": {"type": "number", "minimum": 0},
                "holding_period": {"type": "integer", "minimum": 1}
            }
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "log_dir": {"type": "string"},
                "console_output": {"type": "boolean"}
            }
        },
        "output": {
            "type": "object",
            "properties": {
                "report_dir": {"type": "string"},
                "plot_results": {"type": "boolean"},
                "save_predictions": {"type": "boolean"},
                "export_format": {"type": "string", "enum": ["csv", "excel", "json"]}
            }
        }
    }
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载并验证配置文件
    
    Args:
        config_path (str, optional): 配置文件路径，默认为项目根目录下的config.yaml
        
    Returns:
        Dict[str, Any]: 配置字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: 配置文件格式错误
        jsonschema.exceptions.ValidationError: 配置文件内容不符合模式定义
    """
    global _config
    
    # 如果未指定配置文件路径，使用默认路径
    if config_path is None:
        config_path = _DEFAULT_CONFIG_PATH
    
    logger.info(f"加载配置文件: {config_path}")
    
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        error_msg = f"配置文件不存在: {config_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        error_msg = f"配置文件格式错误: {e}"
        logger.error(error_msg)
        raise
    
    # 验证配置文件内容
    try:
        jsonschema.validate(instance=config, schema=_CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        error_msg = f"配置文件内容不符合模式定义: {e}"
        logger.error(error_msg)
        raise
    
    # 设置全局配置
    _config = config
    
    # 处理路径配置，确保所有目录存在
    _ensure_directories_exist(config)
    
    logger.info("配置文件加载成功")
    return config

def _ensure_directories_exist(config: Dict[str, Any]) -> None:
    """
    确保配置中指定的所有目录都存在，如果不存在则创建
    
    Args:
        config (Dict[str, Any]): 配置字典
    """
    # 数据缓存目录
    if 'data_source' in config and 'cache_dir' in config['data_source']:
        os.makedirs(config['data_source']['cache_dir'], exist_ok=True)
    
    # LLM缓存目录
    if 'llm' in config and 'cache_dir' in config['llm']:
        os.makedirs(config['llm']['cache_dir'], exist_ok=True)
    
    # 模型保存目录
    if 'model' in config and 'model_save_path' in config['model']:
        model_dir = os.path.dirname(config['model']['model_save_path'])
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
    
    # 日志目录
    if 'logging' in config and 'log_dir' in config['logging']:
        os.makedirs(config['logging']['log_dir'], exist_ok=True)
    
    # 报告输出目录
    if 'output' in config and 'report_dir' in config['output']:
        os.makedirs(config['output']['report_dir'], exist_ok=True)

def get_config(section: Optional[str] = None) -> Dict[str, Any]:
    """
    获取配置信息
    
    Args:
        section (str, optional): 配置节名称，如果为None则返回整个配置字典
        
    Returns:
        Dict[str, Any]: 配置字典或指定节的配置
        
    Raises:
        KeyError: 指定的配置节不存在
    """
    global _config
    
    # 如果配置尚未加载，先加载配置
    if not _config:
        load_config()
    
    # 如果未指定配置节，返回整个配置字典
    if section is None:
        return _config
    
    # 检查指定的配置节是否存在
    if section not in _config:
        error_msg = f"配置节不存在: {section}"
        logger.error(error_msg)
        raise KeyError(error_msg)
    
    return _config[section]

def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    保存配置到文件
    
    Args:
        config (Dict[str, Any]): 配置字典
        config_path (str, optional): 配置文件路径，默认为项目根目录下的config.yaml
        
    Raises:
        yaml.YAMLError: 配置保存失败
    """
    global _config
    
    # 如果未指定配置文件路径，使用默认路径
    if config_path is None:
        config_path = _DEFAULT_CONFIG_PATH
    
    # 验证配置内容
    try:
        jsonschema.validate(instance=config, schema=_CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        error_msg = f"配置内容不符合模式定义: {e}"
        logger.error(error_msg)
        raise
    
    # 保存配置到文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        error_msg = f"配置保存失败: {e}"
        logger.error(error_msg)
        raise
    
    # 更新全局配置
    _config = config
    
    logger.info(f"配置已保存到: {config_path}")

def update_config(section: str, key: str, value: Any) -> None:
    """
    更新配置项
    
    Args:
        section (str): 配置节名称
        key (str): 配置项名称
        value (Any): 配置项值
        
    Raises:
        KeyError: 指定的配置节或配置项不存在
    """
    global _config
    
    # 如果配置尚未加载，先加载配置
    if not _config:
        load_config()
    
    # 检查指定的配置节是否存在
    if section not in _config:
        error_msg = f"配置节不存在: {section}"
        logger.error(error_msg)
        raise KeyError(error_msg)
    
    # 更新配置项
    _config[section][key] = value
    
    # 验证更新后的配置
    try:
        jsonschema.validate(instance=_config, schema=_CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        # 如果验证失败，回滚更新
        del _config[section][key]
        error_msg = f"配置更新后不符合模式定义: {e}"
        logger.error(error_msg)
        raise
    
    logger.info(f"配置已更新: {section}.{key} = {value}")

# 测试代码
if __name__ == '__main__':
    # 创建一个示例配置文件
    example_config = {
        "data_source": {
            "api_key": "your_api_key",
            "api_url": "https://api.example.com",
            "start_date": "20200101",
            "end_date": "20231231",
            "stock_pool": ["000001.SZ", "600000.SH"],
            "index_pool": ["000300.SH", "000905.SH"],
            "cache_dir": "./data/cache"
        },
        "features": {
            "technical_indicators": ["MA", "RSI", "MACD"],
            "fundamental_indicators": ["PE", "PB", "ROE"],
            "selection_method": "correlation",
            "top_n_features": 10
        },
        "model": {
            "type": "xgboost",
            "params": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5
            },
            "train_test_split": 0.8,
            "cv_folds": 5,
            "target_variable": "return_5d",
            "model_save_path": "./models/xgboost_model.pkl"
        },
        "llm": {
            "api_key": "your_llm_api_key",
            "model_name": "gpt-4",
            "news_sources": ["sina", "eastmoney", "cnstock"],
            "max_tokens": 1000,
            "temperature": 0.7,
            "cache_dir": "./data/llm_cache"
        },
        "backtest": {
            "initial_capital": 1000000,
            "commission_rate": 0.0003,
            "slippage": 0.0001,
            "benchmark": "000300.SH",
            "rebalance_frequency": "weekly",
            "risk_free_rate": 0.03
        },
        "strategy": {
            "max_positions": 10,
            "position_sizing": "equal",
            "stop_loss": 0.05,
            "take_profit": 0.1,
            "holding_period": 5
        },
        "logging": {
            "level": "INFO",
            "log_dir": "./logs",
            "console_output": True
        },
        "output": {
            "report_dir": "./reports",
            "plot_results": True,
            "save_predictions": True,
            "export_format": "csv"
        }
    }
    
    # 保存示例配置到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp:
        temp_path = temp.name
        yaml.dump(example_config, temp, default_flow_style=False, allow_unicode=True)
    
    try:
        # 测试加载配置
        config = load_config(temp_path)
        print("配置加载成功!")
        
        # 测试获取配置节
        data_source_config = get_config('data_source')
        print(f"数据源配置: {data_source_config}")
        
        # 测试更新配置
        update_config('model', 'cv_folds', 10)
        print(f"更新后的模型配置: {get_config('model')}")
        
        # 测试保存配置
        save_config(config, temp_path)
        print("配置保存成功!")
    finally:
        # 删除临时文件
        os.unlink(temp_path)