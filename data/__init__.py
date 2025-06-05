"""数据模块

提供多种数据源的统一接口，支持：
- tushare API
- 东方财富 API
- 新浪财经 API
- 本地CSV数据
- 数据缓存机制
"""

from .manager import DataManager
from .sources import TushareSource, SinaSource, EastMoneySource, CSVSource
from .cache import DataCache

__all__ = [
    'DataManager',
    'TushareSource',
    'SinaSource', 
    'EastMoneySource',
    'CSVSource',
    'DataCache'
]