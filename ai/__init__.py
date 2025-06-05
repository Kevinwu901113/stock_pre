"""AI模块

为量化选股系统提供AI相关功能，包括：
- 推荐理由生成
- 策略辅助分析
- 智能预测模型
- 自然语言处理
"""

from .model_manager import ModelManager
from .recommendation_generator import RecommendationGenerator
from .strategy_analyzer import StrategyAnalyzer
from .nlp_processor import NLPProcessor

__all__ = [
    'ModelManager',
    'RecommendationGenerator', 
    'StrategyAnalyzer',
    'NLPProcessor'
]