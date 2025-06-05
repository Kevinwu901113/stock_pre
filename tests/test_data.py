import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from data.manager import DataManager
from data.sources.base import BaseDataSource
from data.sources.tushare_source import TushareDataSource
from data.cache import DataCache


class MockDataSource(BaseDataSource):
    """模拟数据源"""
    
    def __init__(self):
        super().__init__()
        self.name = "MockDataSource"
    
    async def get_stock_list(self):
        """获取股票列表"""
        return pd.DataFrame({
            'ts_code': ['000001.SZ', '000002.SZ', '600000.SH'],
            'symbol': ['000001', '000002', '600000'],
            'name': ['平安银行', '万科A', '浦发银行'],
            'area': ['深圳', '深圳', '上海'],
            'industry': ['银行', '房地产', '银行'],
            'market': ['主板', '主板', '主板'],
            'list_date': ['19910403', '19910129', '19990810']
        })
    
    async def get_daily_data(self, ts_code, start_date=None, end_date=None):
        """获取日K线数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
        data = []
        
        for i, date in enumerate(dates):
            base_price = 10 + i * 0.1
            data.append({
                'ts_code': ts_code,
                'trade_date': date.strftime('%Y%m%d'),
                'open': base_price,
                'high': base_price * 1.02,
                'low': base_price * 0.98,
                'close': base_price * 1.01,
                'pre_close': base_price - 0.1,
                'change': 0.1,
                'pct_chg': 1.0,
                'vol': 1000000,
                'amount': base_price * 1000000
            })
        
        return pd.DataFrame(data)
    
    async def get_basic_info(self, ts_code):
        """获取基本信息"""
        return {
            'ts_code': ts_code,
            'name': '测试股票',
            'industry': '测试行业',
            'market': '主板',
            'pe': 15.5,
            'pb': 1.2,
            'total_mv': 50000000,
            'circ_mv': 40000000
        }
    
    async def get_financial_data(self, ts_code, period=None):
        """获取财务数据"""
        return pd.DataFrame({
            'ts_code': [ts_code],
            'end_date': ['20231231'],
            'total_revenue': [1000000000],
            'net_profit': [100000000],
            'total_assets': [5000000000],
            'total_hldr_eqy_exc_min_int': [2000000000],
            'roe': [0.15],
            'roa': [0.05],
            'debt_to_assets': [0.3]
        })


class TestDataManager:
    """数据管理器测试"""
    
    @pytest.fixture
    def mock_cache(self):
        """模拟缓存"""
        cache = Mock(spec=DataCache)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.delete = AsyncMock()
        cache.clear = AsyncMock()
        return cache
    
    @pytest.fixture
    def mock_data_source(self):
        """模拟数据源"""
        return MockDataSource()
    
    @pytest.fixture
    def data_manager(self, mock_cache, mock_data_source):
        """数据管理器实例"""
        manager = DataManager()
        manager.cache = mock_cache
        manager.data_sources = {'mock': mock_data_source}
        manager.primary_source = 'mock'
        return manager
    
    def test_data_manager_initialization(self):
        """测试数据管理器初始化"""
        manager = DataManager()
        assert manager.data_sources == {}
        assert manager.primary_source is None
        assert manager.cache is not None
    
    def test_add_data_source(self, data_manager, mock_data_source):
        """测试添加数据源"""
        data_manager.add_data_source('test', mock_data_source)
        assert 'test' in data_manager.data_sources
        assert data_manager.data_sources['test'] == mock_data_source
    
    def test_set_primary_source(self, data_manager):
        """测试设置主数据源"""
        data_manager.set_primary_source('mock')
        assert data_manager.primary_source == 'mock'
        
        # 测试设置不存在的数据源
        with pytest.raises(ValueError):
            data_manager.set_primary_source('nonexistent')
    
    @pytest.mark.asyncio
    async def test_get_stock_list(self, data_manager):
        """测试获取股票列表"""
        result = await data_manager.get_stock_list()
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'ts_code' in result.columns
        assert 'name' in result.columns
    
    @pytest.mark.asyncio
    async def test_get_stock_data(self, data_manager):
        """测试获取股票数据"""
        result = await data_manager.get_stock_data(
            '000001.SZ',
            start_date='2023-01-01',
            end_date='2023-01-10'
        )
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'ts_code' in result.columns
        assert 'close' in result.columns
    
    @pytest.mark.asyncio
    async def test_get_stock_basic_info(self, data_manager):
        """测试获取股票基本信息"""
        result = await data_manager.get_stock_basic_info('000001.SZ')
        
        assert isinstance(result, dict)
        assert 'ts_code' in result
        assert 'name' in result
    
    @pytest.mark.asyncio
    async def test_get_financial_data(self, data_manager):
        """测试获取财务数据"""
        result = await data_manager.get_financial_data('000001.SZ')
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'ts_code' in result.columns
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, data_manager, mock_cache):
        """测试缓存集成"""
        # 第一次调用，缓存为空
        mock_cache.get.return_value = None
        result1 = await data_manager.get_stock_list()
        
        # 验证缓存被调用
        mock_cache.get.assert_called()
        mock_cache.set.assert_called()
        
        # 第二次调用，返回缓存数据
        cached_data = result1.copy()
        mock_cache.get.return_value = cached_data
        result2 = await data_manager.get_stock_list()
        
        # 验证返回的是缓存数据
        pd.testing.assert_frame_equal(result2, cached_data)
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, data_manager):
        """测试数据源故障转移机制"""
        # 添加一个会失败的数据源作为主数据源
        failing_source = Mock(spec=BaseDataSource)
        failing_source.get_stock_list = AsyncMock(side_effect=Exception("Connection failed"))
        
        # 添加备用数据源
        backup_source = MockDataSource()
        
        data_manager.add_data_source('failing', failing_source)
        data_manager.add_data_source('backup', backup_source)
        data_manager.set_primary_source('failing')
        
        # 应该自动切换到备用数据源
        result = await data_manager.get_stock_list()
        assert isinstance(result, pd.DataFrame)
        assert not result.empty


class TestTushareDataSource:
    """Tushare数据源测试"""
    
    @pytest.fixture
    def tushare_source(self):
        """Tushare数据源实例"""
        with patch('tushare.set_token'):
            source = TushareDataSource(token='test_token')
            return source
    
    def test_tushare_initialization(self, tushare_source):
        """测试Tushare初始化"""
        assert tushare_source.name == 'TushareDataSource'
        assert tushare_source.token == 'test_token'
    
    @pytest.mark.asyncio
    async def test_get_stock_list_with_mock(self, tushare_source):
        """测试获取股票列表（模拟）"""
        mock_data = pd.DataFrame({
            'ts_code': ['000001.SZ', '000002.SZ'],
            'symbol': ['000001', '000002'],
            'name': ['平安银行', '万科A'],
            'area': ['深圳', '深圳'],
            'industry': ['银行', '房地产'],
            'market': ['主板', '主板']
        })
        
        with patch.object(tushare_source, '_fetch_data', return_value=mock_data):
            result = await tushare_source.get_stock_list()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert 'ts_code' in result.columns
    
    @pytest.mark.asyncio
    async def test_get_daily_data_with_mock(self, tushare_source):
        """测试获取日K线数据（模拟）"""
        mock_data = pd.DataFrame({
            'ts_code': ['000001.SZ'] * 5,
            'trade_date': ['20230101', '20230102', '20230103', '20230104', '20230105'],
            'open': [10.0, 10.1, 10.2, 10.3, 10.4],
            'high': [10.2, 10.3, 10.4, 10.5, 10.6],
            'low': [9.8, 9.9, 10.0, 10.1, 10.2],
            'close': [10.1, 10.2, 10.3, 10.4, 10.5],
            'vol': [1000000] * 5,
            'amount': [10100000, 10200000, 10300000, 10400000, 10500000]
        })
        
        with patch.object(tushare_source, '_fetch_data', return_value=mock_data):
            result = await tushare_source.get_daily_data('000001.SZ')
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 5
            assert 'close' in result.columns
    
    def test_rate_limiting(self, tushare_source):
        """测试API调用频率限制"""
        # 测试频率限制逻辑
        assert hasattr(tushare_source, '_last_call_time')
        assert hasattr(tushare_source, '_min_interval')
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tushare_source):
        """测试错误处理"""
        with patch.object(tushare_source, '_fetch_data', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await tushare_source.get_stock_list()


class TestDataCache:
    """数据缓存测试"""
    
    @pytest.fixture
    def cache(self):
        """缓存实例"""
        return DataCache()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, cache):
        """测试缓存基本操作"""
        key = 'test_key'
        value = {'test': 'data'}
        
        # 测试设置和获取
        await cache.set(key, value)
        result = await cache.get(key)
        assert result == value
        
        # 测试删除
        await cache.delete(key)
        result = await cache.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """测试缓存过期"""
        key = 'expire_test'
        value = {'test': 'data'}
        
        # 设置很短的过期时间
        await cache.set(key, value, ttl=1)
        
        # 立即获取应该有数据
        result = await cache.get(key)
        assert result == value
        
        # 等待过期
        await asyncio.sleep(2)
        result = await cache.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """测试清空缓存"""
        # 设置多个键值对
        await cache.set('key1', 'value1')
        await cache.set('key2', 'value2')
        
        # 清空缓存
        await cache.clear()
        
        # 验证所有数据都被清空
        assert await cache.get('key1') is None
        assert await cache.get('key2') is None


class TestDataIntegration:
    """数据模块集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self):
        """测试端到端数据流"""
        # 创建完整的数据管理器
        manager = DataManager()
        mock_source = MockDataSource()
        manager.add_data_source('mock', mock_source)
        manager.set_primary_source('mock')
        
        # 测试完整的数据获取流程
        stock_list = await manager.get_stock_list()
        assert not stock_list.empty
        
        # 获取第一只股票的数据
        first_stock = stock_list.iloc[0]['ts_code']
        stock_data = await manager.get_stock_data(first_stock)
        assert not stock_data.empty
        
        # 获取基本信息
        basic_info = await manager.get_stock_basic_info(first_stock)
        assert isinstance(basic_info, dict)
        
        # 获取财务数据
        financial_data = await manager.get_financial_data(first_stock)
        assert not financial_data.empty
    
    @pytest.mark.asyncio
    async def test_concurrent_data_access(self):
        """测试并发数据访问"""
        manager = DataManager()
        mock_source = MockDataSource()
        manager.add_data_source('mock', mock_source)
        manager.set_primary_source('mock')
        
        # 并发获取多只股票的数据
        stock_codes = ['000001.SZ', '000002.SZ', '600000.SH']
        
        tasks = []
        for code in stock_codes:
            task = manager.get_stock_data(code)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有结果
        assert len(results) == len(stock_codes)
        for result in results:
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
    
    def test_data_validation(self):
        """测试数据验证"""
        # 测试股票代码格式验证
        valid_codes = ['000001.SZ', '600000.SH', '300001.SZ']
        invalid_codes = ['000001', 'SZ000001', '000001.XX']
        
        for code in valid_codes:
            assert DataManager._validate_stock_code(code)
        
        for code in invalid_codes:
            assert not DataManager._validate_stock_code(code)
    
    def test_date_validation(self):
        """测试日期验证"""
        # 测试日期格式验证
        valid_dates = ['2023-01-01', '2023-12-31']
        invalid_dates = ['2023/01/01', '01-01-2023', '2023-13-01']
        
        for date_str in valid_dates:
            assert DataManager._validate_date(date_str)
        
        for date_str in invalid_dates:
            assert not DataManager._validate_date(date_str)


if __name__ == "__main__":
    pytest.main([__file__])