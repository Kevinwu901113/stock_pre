#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股推荐系统策略模块

该模块负责根据融合后的评分，从股票池中筛选推荐股票
"""

from .buy_strategy import BuyStrategy, TopNStrategy, ThresholdStrategy, RiskControlRule

__all__ = ['BuyStrategy', 'TopNStrategy', 'ThresholdStrategy', 'RiskControlRule']