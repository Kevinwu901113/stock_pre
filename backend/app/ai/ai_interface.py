#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI接口模块
定义AI功能的抽象接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime


class AIProvider(Enum):
    """AI服务提供商枚举"""
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"
    BAIDU = "baidu"
    LOCAL = "local"
    MOCK = "mock"  # 用于测试


@dataclass
class AIRequest:
    """AI请求数据结构"""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AIInterface(ABC):
    """AI服务抽象接口"""
    
    def __init__(self, provider: AIProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化AI服务"""
        pass
    
    @abstractmethod
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        pass
    
    @abstractmethod
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """关键词提取"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    @property
    def provider_name(self) -> str:
        """获取提供商名称"""
        return self.provider.value


class MockAIProvider(AIInterface):
    """模拟AI提供商，用于测试和开发"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AIProvider.MOCK, config or {})
    
    async def initialize(self) -> bool:
        """初始化模拟AI服务"""
        self._initialized = True
        return True
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """生成模拟文本"""
        # 根据prompt生成简单的模拟响应
        if "推荐理由" in request.prompt or "recommendation" in request.prompt.lower():
            content = "基于技术分析，该股票呈现上涨趋势，成交量放大，建议关注。"
        elif "市场分析" in request.prompt or "market" in request.prompt.lower():
            content = "当前市场整体呈现震荡上行态势，建议保持谨慎乐观。"
        elif "风险评估" in request.prompt or "risk" in request.prompt.lower():
            content = "风险等级：中等。建议控制仓位，设置止损。"
        else:
            content = f"这是对您的问题的模拟回答：{request.prompt[:50]}..."
        
        return AIResponse(
            content=content,
            confidence=0.8,
            metadata={"provider": "mock", "model": "mock-model"},
            usage={"tokens": len(content)}
        )
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """模拟情感分析"""
        # 简单的关键词匹配
        positive_words = ["上涨", "利好", "买入", "推荐", "看好"]
        negative_words = ["下跌", "利空", "卖出", "风险", "谨慎"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.7
        elif negative_count > positive_count:
            sentiment = "negative"
            score = 0.3
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.8,
            "details": {
                "positive_words": positive_count,
                "negative_words": negative_count
            }
        }
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """模拟关键词提取"""
        # 简单的关键词提取
        import re
        
        # 移除标点符号并分词
        words = re.findall(r'\b\w+\b', text)
        
        # 过滤常见停用词
        stop_words = {"的", "是", "在", "有", "和", "与", "或", "但", "而", "了", "着", "过"}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频并返回前N个
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    async def health_check(self) -> bool:
        """健康检查"""
        return self._initialized


class AICapabilities:
    """AI能力定义"""
    
    TEXT_GENERATION = "text_generation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    KEYWORD_EXTRACTION = "keyword_extraction"
    MARKET_ANALYSIS = "market_analysis"
    RECOMMENDATION_EXPLANATION = "recommendation_explanation"
    RISK_ASSESSMENT = "risk_assessment"
    NEWS_SUMMARIZATION = "news_summarization"
    TECHNICAL_ANALYSIS = "technical_analysis"


@dataclass
class AIProviderInfo:
    """AI提供商信息"""
    name: str
    provider: AIProvider
    capabilities: List[str]
    max_tokens: int
    cost_per_token: Optional[float] = None
    rate_limit: Optional[Dict[str, int]] = None
    description: Optional[str] = None