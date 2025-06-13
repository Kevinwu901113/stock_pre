#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
买入策略模块

根据融合后的最终评分，从股票池中筛选推荐Top-N股票
支持策略参数配置、排序过滤、风控规则嵌入，结果用于当日尾盘推荐
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Callable, Any
import logging
from abc import ABC, abstractmethod
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskControlRule(ABC):
    """
    风控规则抽象基类
    所有具体风控规则都应继承此类并实现apply方法
    """
    
    def __init__(self, name: str = "base_risk_rule"):
        """
        初始化风控规则
        
        Args:
            name: 规则名称
        """
        self.name = name
    
    @abstractmethod
    def apply(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        应用风控规则
        
        Args:
            stock_data: 股票数据，包含股票代码、评分等信息
            
        Returns:
            过滤后的股票数据
        """
        pass


class VolatilityRule(RiskControlRule):
    """
    波动率风控规则
    过滤掉近期波动率过高的股票
    """
    
    def __init__(self, volatility_window: int = 20, max_volatility: float = 0.03):
        """
        初始化波动率风控规则
        
        Args:
            volatility_window: 计算波动率的窗口期(天数)
            max_volatility: 最大允许波动率
        """
        super().__init__(name="volatility_rule")
        self.volatility_window = volatility_window
        self.max_volatility = max_volatility
    
    def apply(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        应用波动率风控规则
        
        Args:
            stock_data: 股票数据，必须包含'symbol'和'volatility'列
            
        Returns:
            过滤后的股票数据
        """
        if 'volatility' not in stock_data.columns:
            logger.warning("股票数据中缺少波动率(volatility)列，无法应用波动率风控规则")
            return stock_data
        
        # 过滤高波动率股票
        filtered_data = stock_data[stock_data['volatility'] <= self.max_volatility].copy()
        
        # 记录过滤情况
        filtered_count = len(stock_data) - len(filtered_data)
        logger.info(f"波动率风控规则过滤了{filtered_count}只股票，剩余{len(filtered_data)}只")
        
        return filtered_data


class TurnoverRule(RiskControlRule):
    """
    换手率风控规则
    过滤掉换手率过高或过低的股票
    """
    
    def __init__(self, min_turnover: float = 1.0, max_turnover: float = 15.0):
        """
        初始化换手率风控规则
        
        Args:
            min_turnover: 最小换手率(%)
            max_turnover: 最大换手率(%)
        """
        super().__init__(name="turnover_rule")
        self.min_turnover = min_turnover
        self.max_turnover = max_turnover
    
    def apply(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        应用换手率风控规则
        
        Args:
            stock_data: 股票数据，必须包含'symbol'和'turnover'列
            
        Returns:
            过滤后的股票数据
        """
        if 'turnover' not in stock_data.columns:
            logger.warning("股票数据中缺少换手率(turnover)列，无法应用换手率风控规则")
            return stock_data
        
        # 过滤换手率异常股票
        filtered_data = stock_data[
            (stock_data['turnover'] >= self.min_turnover) & 
            (stock_data['turnover'] <= self.max_turnover)
        ].copy()
        
        # 记录过滤情况
        filtered_count = len(stock_data) - len(filtered_data)
        logger.info(f"换手率风控规则过滤了{filtered_count}只股票，剩余{len(filtered_data)}只")
        
        return filtered_data


class PriceRule(RiskControlRule):
    """
    价格风控规则
    过滤掉价格过高或过低的股票
    """
    
    def __init__(self, min_price: float = 5.0, max_price: float = 100.0):
        """
        初始化价格风控规则
        
        Args:
            min_price: 最低价格(元)
            max_price: 最高价格(元)
        """
        super().__init__(name="price_rule")
        self.min_price = min_price
        self.max_price = max_price
    
    def apply(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        应用价格风控规则
        
        Args:
            stock_data: 股票数据，必须包含'symbol'和'close'列
            
        Returns:
            过滤后的股票数据
        """
        if 'close' not in stock_data.columns:
            logger.warning("股票数据中缺少收盘价(close)列，无法应用价格风控规则")
            return stock_data
        
        # 过滤价格异常股票
        filtered_data = stock_data[
            (stock_data['close'] >= self.min_price) & 
            (stock_data['close'] <= self.max_price)
        ].copy()
        
        # 记录过滤情况
        filtered_count = len(stock_data) - len(filtered_data)
        logger.info(f"价格风控规则过滤了{filtered_count}只股票，剩余{len(filtered_data)}只")
        
        return filtered_data


class STRule(RiskControlRule):
    """
    ST股票风控规则
    过滤掉ST、*ST等特殊处理股票
    """
    
    def __init__(self):
        """
        初始化ST股票风控规则
        """
        super().__init__(name="st_rule")
    
    def apply(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        应用ST股票风控规则
        
        Args:
            stock_data: 股票数据，必须包含'symbol'和'name'列
            
        Returns:
            过滤后的股票数据
        """
        if 'name' not in stock_data.columns:
            logger.warning("股票数据中缺少股票名称(name)列，无法应用ST风控规则")
            return stock_data
        
        # 过滤ST股票
        filtered_data = stock_data[~stock_data['name'].str.contains('ST|\*ST')].copy()
        
        # 记录过滤情况
        filtered_count = len(stock_data) - len(filtered_data)
        logger.info(f"ST风控规则过滤了{filtered_count}只股票，剩余{len(filtered_data)}只")
        
        return filtered_data


class BuyStrategy(ABC):
    """
    买入策略抽象基类
    所有具体买入策略都应继承此类并实现select方法
    """
    
    def __init__(self, name: str = "base_strategy"):
        """
        初始化买入策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.risk_rules: List[RiskControlRule] = []
    
    def add_risk_rule(self, rule: RiskControlRule):
        """
        添加风控规则
        
        Args:
            rule: 风控规则实例
        """
        self.risk_rules.append(rule)
        logger.info(f"添加风控规则: {rule.name}")
    
    def apply_risk_rules(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        应用所有风控规则
        
        Args:
            stock_data: 股票数据
            
        Returns:
            应用风控规则后的股票数据
        """
        filtered_data = stock_data.copy()
        
        for rule in self.risk_rules:
            filtered_data = rule.apply(filtered_data)
        
        return filtered_data
    
    @abstractmethod
    def select(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        选股方法
        
        Args:
            stock_data: 股票数据，包含股票代码、评分等信息
            
        Returns:
            选中的股票数据
        """
        pass
    
    def recommend(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        推荐股票
        
        Args:
            stock_data: 股票数据，包含股票代码、评分等信息
            
        Returns:
            推荐的股票数据
        """
        # 1. 应用风控规则
        filtered_data = self.apply_risk_rules(stock_data)
        
        # 2. 应用选股策略
        selected_stocks = self.select(filtered_data)
        
        # 3. 添加推荐时间
        selected_stocks['recommend_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
        selected_stocks['strategy_name'] = self.name
        
        return selected_stocks


class TopNStrategy(BuyStrategy):
    """
    Top-N选股策略
    选择评分最高的N只股票
    """
    
    def __init__(self, top_n: int = 10, score_column: str = 'final_score'):
        """
        初始化Top-N选股策略
        
        Args:
            top_n: 选择的股票数量
            score_column: 评分列名
        """
        super().__init__(name=f"top_{top_n}_strategy")
        self.top_n = top_n
        self.score_column = score_column
    
    def select(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        选择评分最高的N只股票
        
        Args:
            stock_data: 股票数据，必须包含self.score_column指定的评分列
            
        Returns:
            选中的股票数据
        """
        if self.score_column not in stock_data.columns:
            logger.error(f"股票数据中缺少评分列{self.score_column}，无法应用Top-N策略")
            return pd.DataFrame()
        
        # 按评分降序排序并选择前N只
        selected = stock_data.sort_values(by=self.score_column, ascending=False).head(self.top_n).copy()
        
        logger.info(f"Top-{self.top_n}策略选出{len(selected)}只股票")
        
        return selected


class ThresholdStrategy(BuyStrategy):
    """
    阈值选股策略
    选择评分高于阈值的股票
    """
    
    def __init__(self, threshold: float = 80.0, score_column: str = 'final_score', max_stocks: int = 20):
        """
        初始化阈值选股策略
        
        Args:
            threshold: 评分阈值
            score_column: 评分列名
            max_stocks: 最大选股数量
        """
        super().__init__(name=f"threshold_{threshold}_strategy")
        self.threshold = threshold
        self.score_column = score_column
        self.max_stocks = max_stocks
    
    def select(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        选择评分高于阈值的股票
        
        Args:
            stock_data: 股票数据，必须包含self.score_column指定的评分列
            
        Returns:
            选中的股票数据
        """
        if self.score_column not in stock_data.columns:
            logger.error(f"股票数据中缺少评分列{self.score_column}，无法应用阈值策略")
            return pd.DataFrame()
        
        # 选择评分高于阈值的股票
        selected = stock_data[stock_data[self.score_column] >= self.threshold].copy()
        
        # 如果超过最大数量，则取评分最高的max_stocks只
        if len(selected) > self.max_stocks:
            selected = selected.sort_values(by=self.score_column, ascending=False).head(self.max_stocks)
        
        logger.info(f"阈值{self.threshold}策略选出{len(selected)}只股票")
        
        return selected


class SectorBalancedStrategy(BuyStrategy):
    """
    行业均衡选股策略
    在保证评分的基础上，实现行业分散
    """
    
    def __init__(self, top_n: int = 10, sector_limit: int = 2, score_column: str = 'final_score', sector_column: str = 'sector'):
        """
        初始化行业均衡选股策略
        
        Args:
            top_n: 选择的股票总数量
            sector_limit: 每个行业最多选择的股票数量
            score_column: 评分列名
            sector_column: 行业列名
        """
        super().__init__(name=f"sector_balanced_strategy")
        self.top_n = top_n
        self.sector_limit = sector_limit
        self.score_column = score_column
        self.sector_column = sector_column
    
    def select(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        选择评分高且行业分散的股票
        
        Args:
            stock_data: 股票数据，必须包含评分列和行业列
            
        Returns:
            选中的股票数据
        """
        if self.score_column not in stock_data.columns:
            logger.error(f"股票数据中缺少评分列{self.score_column}，无法应用行业均衡策略")
            return pd.DataFrame()
        
        if self.sector_column not in stock_data.columns:
            logger.error(f"股票数据中缺少行业列{self.sector_column}，无法应用行业均衡策略")
            return pd.DataFrame()
        
        # 按评分降序排序
        sorted_data = stock_data.sort_values(by=self.score_column, ascending=False).copy()
        
        # 行业计数器
        sector_counts = {}
        selected_indices = []
        
        # 遍历排序后的股票
        for idx, row in sorted_data.iterrows():
            sector = row[self.sector_column]
            
            # 如果该行业还未达到上限，则选择该股票
            if sector_counts.get(sector, 0) < self.sector_limit:
                selected_indices.append(idx)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
            
            # 如果已选择足够数量的股票，则结束
            if len(selected_indices) >= self.top_n:
                break
        
        # 获取选中的股票
        selected = stock_data.loc[selected_indices].copy()
        
        logger.info(f"行业均衡策略选出{len(selected)}只股票，覆盖{len(sector_counts)}个行业")
        
        return selected