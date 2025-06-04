#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模块
为AI功能集成预留接口
"""

from .ai_interface import AIInterface, AIProvider
from .recommendation_explainer import RecommendationExplainer
from .market_analyzer import MarketAnalyzer
from .ai_factory import AIFactory

__all__ = [
    "AIInterface",
    "AIProvider", 
    "RecommendationExplainer",
    "MarketAnalyzer",
    "AIFactory"
]