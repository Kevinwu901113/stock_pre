#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略模块
"""

from .base_strategy import BaseStrategy
from .evening_buy_strategy import EveningBuyStrategy
from .morning_sell_strategy import MorningSellStrategy

__all__ = [
    "BaseStrategy",
    "EveningBuyStrategy",
    "MorningSellStrategy"
]