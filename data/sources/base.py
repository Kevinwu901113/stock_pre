"""数据源基类

定义所有数据源必须实现的接口和通用功能。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import asyncio
from loguru import logger


class BaseDataSource(ABC):
    """数据源基类
    
    所有数据源都应该继承这个基类并实现必要的方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据源
        
        Args:
            config: 数据源配置
        """
        self.config = config
        self.name = self.__class__.__name__.replace('Source', '').lower()
        self.enabled = config.get('enabled', False)
        self.rate_limit = config.get('rate_limit', 100)  # 每分钟请求限制
        self.priority = config.get('priority', 999)
        self.logger = logger.bind(source=self.name)
        
        # 请求计数器（用于限流）
        self._request_count = 0
        self._last_reset_time = datetime.now()
    
    def _check_rate_limit(self) -> bool:
        """检查是否超过请求限制
        
        Returns:
            是否可以继续请求
        """
        now = datetime.now()
        
        # 每分钟重置计数器
        if (now - self._last_reset_time).seconds >= 60:
            self._request_count = 0
            self._last_reset_time = now
        
        if self._request_count >= self.rate_limit:
            self.logger.warning(f"达到请求限制 {self.rate_limit}/分钟")
            return False
        
        self._request_count += 1
        return True
    
    @abstractmethod
    async def get_stock_list(self, market: str = 'A') -> List[Dict[str, Any]]:
        """获取股票列表
        
        Args:
            market: 市场类型 ('A', 'HK', 'US')
            
        Returns:
            股票列表，每个元素包含：
            - code: 股票代码
            - name: 股票名称
            - market: 市场
            - industry: 行业
            - list_date: 上市日期
        """
        pass
    
    @abstractmethod
    async def get_stock_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        period: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """获取股票历史数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期 ('daily', '5min', '15min', '30min', '60min')
            
        Returns:
            股票数据列表，每个元素包含：
            - date: 日期
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
        """
        pass
    
    @abstractmethod
    async def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时行情数据
        
        Args:
            codes: 股票代码列表
            
        Returns:
            实时数据字典，键为股票代码，值包含：
            - current_price: 当前价格
            - change: 涨跌额
            - change_pct: 涨跌幅
            - volume: 成交量
            - amount: 成交额
            - high: 最高价
            - low: 最低价
            - open: 开盘价
            - prev_close: 昨收价
        """
        pass
    
    async def get_market_data(
        self,
        index_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """获取市场指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据列表，每个元素包含：
            - date: 日期
            - open: 开盘点数
            - high: 最高点数
            - low: 最低点数
            - close: 收盘点数
            - volume: 成交量
            - amount: 成交额
            - change_pct: 涨跌幅
        """
        # 默认实现：将指数当作股票处理
        return await self.get_stock_data(index_code, start_date, end_date)
    
    async def get_fundamental_data(self, code: str) -> Dict[str, Any]:
        """获取基本面数据
        
        Args:
            code: 股票代码
            
        Returns:
            基本面数据，包含：
            - pe_ratio: 市盈率
            - pb_ratio: 市净率
            - market_cap: 市值
            - total_share: 总股本
            - float_share: 流通股本
            - revenue: 营业收入
            - net_profit: 净利润
            - roe: 净资产收益率
            - debt_ratio: 资产负债率
        """
        # 默认实现：返回空字典
        self.logger.warning(f"数据源 {self.name} 不支持基本面数据")
        return {}
    
    async def get_financial_data(
        self,
        code: str,
        report_type: str = 'annual'
    ) -> List[Dict[str, Any]]:
        """获取财务数据
        
        Args:
            code: 股票代码
            report_type: 报告类型 ('annual', 'quarterly')
            
        Returns:
            财务数据列表
        """
        # 默认实现：返回空列表
        self.logger.warning(f"数据源 {self.name} 不支持财务数据")
        return []
    
    async def get_industry_data(self) -> List[Dict[str, Any]]:
        """获取行业分类数据
        
        Returns:
            行业数据列表，每个元素包含：
            - industry_code: 行业代码
            - industry_name: 行业名称
            - parent_code: 父级行业代码
            - level: 层级
        """
        # 默认实现：返回空列表
        self.logger.warning(f"数据源 {self.name} 不支持行业数据")
        return []
    
    async def get_concept_data(self) -> List[Dict[str, Any]]:
        """获取概念板块数据
        
        Returns:
            概念数据列表
        """
        # 默认实现：返回空列表
        self.logger.warning(f"数据源 {self.name} 不支持概念数据")
        return []
    
    async def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票
        
        Args:
            keyword: 搜索关键词（股票代码或名称）
            
        Returns:
            搜索结果列表
        """
        # 默认实现：从股票列表中搜索
        try:
            stock_list = await self.get_stock_list()
            results = []
            
            keyword = keyword.upper().strip()
            
            for stock in stock_list:
                if (keyword in stock.get('code', '').upper() or 
                    keyword in stock.get('name', '')):
                    results.append(stock)
                    
                if len(results) >= 20:  # 限制返回数量
                    break
                    
            return results
            
        except Exception as e:
            self.logger.error(f"搜索股票失败: {e}")
            return []
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            数据源是否健康
        """
        try:
            # 尝试获取少量数据进行测试
            test_data = await self.get_stock_list()
            return len(test_data) > 0
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """获取数据源信息
        
        Returns:
            数据源信息
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'rate_limit': self.rate_limit,
            'priority': self.priority,
            'request_count': self._request_count,
            'last_reset_time': self._last_reset_time.isoformat()
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 清理资源
        pass