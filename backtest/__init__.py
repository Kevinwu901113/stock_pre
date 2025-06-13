#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股回测模块
提供历史模拟交易和策略评估功能
"""

from .simulator import BacktestSimulator
from .evaluator import BacktestEvaluator

__all__ = ['BacktestSimulator', 'BacktestEvaluator']