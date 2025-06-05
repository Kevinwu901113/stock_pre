"""数据源模块

提供多种数据源的实现：
- Tushare数据源
- 新浪财经数据源
- 东方财富数据源
- CSV文件数据源
"""

from .base import BaseDataSource
from .tushare_source import TushareSource
from .sina_source import SinaSource
from .eastmoney_source import EastMoneySource
from .csv_source import CSVSource

__all__ = [
    'BaseDataSource',
    'TushareSource',
    'SinaSource',
    'EastMoneySource',
    'CSVSource'
]