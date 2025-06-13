#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusion模块

该模块负责融合来自不同模型的评分，提供统一的评分融合功能。
"""

from .score_fusion import (
    ScoreFusion,
    FusionStrategy,
    WeightedAverageStrategy,
    GeometricMeanStrategy,
    HarmonicMeanStrategy,
    MaxStrategy,
    MinStrategy,
    CustomFormulaStrategy,
    create_custom_formula_example
)

__version__ = "1.0.0"
__author__ = "Stock Recommendation System"

__all__ = [
    'ScoreFusion',
    'FusionStrategy',
    'WeightedAverageStrategy',
    'GeometricMeanStrategy',
    'HarmonicMeanStrategy',
    'MaxStrategy',
    'MinStrategy',
    'CustomFormulaStrategy',
    'create_custom_formula_example'
]