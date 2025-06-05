import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock

from strategies.base import BaseStrategy
from strategies.technical import MovingAverageCrossStrategy
from strategies.fundamental import ValueInvestmentStrategy


class MockDatabase:
    """模拟数据库"""
    
    def __init__(self):
        self.stock_prices = self._generate_mock_price_data()
        self.stock_fundamentals = self._generate_mock_fundamental_data()
    
    def _generate_mock_price_data(self):
        """生成模拟价格数据"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        data = []
        
        for i, date in enumerate(dates):
            # 生成模拟的OHLCV数据
            base_price = 10 + (i % 100) * 0.1
            data.append({
                'date': date.date(),
                'open': base_price,
                'high': base_price * 1.02,
                'low': base_price * 0.98,
                'close': base_price * (1 + (i % 10 - 5) * 0.01),
                'volume': 1000000 + (i % 500000),
                'amount': base_price * (1000000 + (i % 500000))
            })
        
        return pd.DataFrame(data)
    
    def _generate_mock_fundamental_data(self):
        """生成模拟基本面数据"""
        return {
            'pe_ratio': 15.5,
            'pb_ratio': 1.2,
            'market_cap': 50000000000,
            'roe': 0.15,
            'debt_ratio': 0.3
        }


class TestBaseStrategy:
    """基础策略测试"""
    
    def test_strategy_interface(self):
        """测试策略接口"""
        # 测试抽象基类不能直接实例化
        with pytest.raises(TypeError):
            BaseStrategy(Mock(), {})
    
    def test_strategy_inheritance(self):
        """测试策略继承"""
        # 确保具体策略类正确继承了基类
        assert issubclass(MovingAverageCrossStrategy, BaseStrategy)
        assert issubclass(ValueInvestmentStrategy, BaseStrategy)


class TestMovingAverageCrossStrategy:
    """移动平均线交叉策略测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        return MockDatabase()
    
    @pytest.fixture
    def strategy(self, mock_db):
        """策略实例"""
        parameters = {
            'short_period': 5,
            'long_period': 20,
            'volume_threshold': 1.5,
            'min_confidence': 0.6
        }
        return MovingAverageCrossStrategy(mock_db, parameters)
    
    def test_strategy_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.name == 'MovingAverageCrossStrategy'
        assert strategy.parameters['short_period'] == 5
        assert strategy.parameters['long_period'] == 20
    
    def test_get_description(self, strategy):
        """测试获取策略描述"""
        description = strategy.get_description()
        assert isinstance(description, str)
        assert len(description) > 0
    
    def test_get_parameters_schema(self, strategy):
        """测试获取参数模式"""
        schema = strategy.get_parameters_schema()
        assert isinstance(schema, dict)
        assert 'short_period' in schema
        assert 'long_period' in schema
        assert 'volume_threshold' in schema
        assert 'min_confidence' in schema
    
    @pytest.mark.asyncio
    async def test_execute_strategy(self, strategy, mock_db):
        """测试策略执行"""
        # 模拟策略执行
        stock_codes = ['000001.SZ', '000002.SZ']
        
        # 由于这是集成测试，我们需要模拟数据获取
        with pytest.MonkeyPatch().context() as m:
            # 模拟数据获取方法
            async def mock_get_stock_prices(*args, **kwargs):
                return mock_db.stock_prices
            
            m.setattr(strategy, '_get_stock_prices', mock_get_stock_prices)
            
            results = await strategy.execute(stock_codes)
            
            assert isinstance(results, list)
            for result in results:
                assert 'stock_code' in result
                assert 'signal' in result
                assert 'confidence' in result
                assert 'reason' in result
                assert result['signal'] in ['buy', 'sell', 'hold']
                assert 0 <= result['confidence'] <= 1
    
    def test_calculate_moving_averages(self, strategy, mock_db):
        """测试移动平均线计算"""
        prices = mock_db.stock_prices['close'].values
        
        # 测试短期移动平均线
        short_ma = strategy._calculate_moving_average(prices, 5)
        assert len(short_ma) == len(prices)
        assert not pd.isna(short_ma[-1])  # 最后一个值不应该是NaN
        
        # 测试长期移动平均线
        long_ma = strategy._calculate_moving_average(prices, 20)
        assert len(long_ma) == len(prices)
    
    def test_detect_cross_signals(self, strategy):
        """测试交叉信号检测"""
        # 创建测试数据：短期均线上穿长期均线
        short_ma = pd.Series([9.8, 9.9, 10.0, 10.1, 10.2])
        long_ma = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0])
        
        signal = strategy._detect_cross_signal(short_ma, long_ma)
        assert signal in ['buy', 'sell', 'hold']
    
    def test_calculate_confidence(self, strategy, mock_db):
        """测试置信度计算"""
        price_data = mock_db.stock_prices
        signal = 'buy'
        
        confidence = strategy._calculate_confidence(price_data, signal)
        assert 0 <= confidence <= 1


class TestValueInvestmentStrategy:
    """价值投资策略测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        return MockDatabase()
    
    @pytest.fixture
    def strategy(self, mock_db):
        """策略实例"""
        parameters = {
            'max_pe_ratio': 20,
            'max_pb_ratio': 2.0,
            'min_roe': 0.1,
            'max_debt_ratio': 0.5,
            'min_confidence': 0.7
        }
        return ValueInvestmentStrategy(mock_db, parameters)
    
    def test_strategy_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.name == 'ValueInvestmentStrategy'
        assert strategy.parameters['max_pe_ratio'] == 20
        assert strategy.parameters['min_roe'] == 0.1
    
    @pytest.mark.asyncio
    async def test_execute_strategy(self, strategy, mock_db):
        """测试策略执行"""
        stock_codes = ['000001.SZ']
        
        with pytest.MonkeyPatch().context() as m:
            # 模拟数据获取方法
            async def mock_get_fundamentals(*args, **kwargs):
                return mock_db.stock_fundamentals
            
            m.setattr(strategy, '_get_stock_fundamentals', mock_get_fundamentals)
            
            results = await strategy.execute(stock_codes)
            
            assert isinstance(results, list)
            if results:  # 如果有结果
                result = results[0]
                assert 'stock_code' in result
                assert 'signal' in result
                assert 'confidence' in result
                assert 'reason' in result
    
    def test_evaluate_value_metrics(self, strategy, mock_db):
        """测试价值指标评估"""
        fundamentals = mock_db.stock_fundamentals
        
        score = strategy._evaluate_value_metrics(fundamentals)
        assert 0 <= score <= 1
    
    def test_pe_ratio_evaluation(self, strategy):
        """测试市盈率评估"""
        # 测试低市盈率（好）
        score_low = strategy._evaluate_pe_ratio(10)
        assert score_low > 0.5
        
        # 测试高市盈率（差）
        score_high = strategy._evaluate_pe_ratio(50)
        assert score_high < 0.5
    
    def test_pb_ratio_evaluation(self, strategy):
        """测试市净率评估"""
        # 测试低市净率（好）
        score_low = strategy._evaluate_pb_ratio(0.8)
        assert score_low > 0.5
        
        # 测试高市净率（差）
        score_high = strategy._evaluate_pb_ratio(3.0)
        assert score_high < 0.5


class TestStrategyPerformance:
    """策略性能测试"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDatabase()
    
    @pytest.mark.asyncio
    async def test_strategy_execution_time(self, mock_db):
        """测试策略执行时间"""
        strategy = MovingAverageCrossStrategy(mock_db, {
            'short_period': 5,
            'long_period': 20
        })
        
        start_time = datetime.now()
        
        # 模拟执行
        with pytest.MonkeyPatch().context() as m:
            async def mock_get_stock_prices(*args, **kwargs):
                return mock_db.stock_prices
            
            m.setattr(strategy, '_get_stock_prices', mock_get_stock_prices)
            
            await strategy.execute(['000001.SZ'])
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 策略执行应该在合理时间内完成（比如1秒）
        assert execution_time < 1.0
    
    def test_strategy_memory_usage(self, mock_db):
        """测试策略内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建多个策略实例
        strategies = []
        for i in range(10):
            strategy = MovingAverageCrossStrategy(mock_db, {
                'short_period': 5,
                'long_period': 20
            })
            strategies.append(strategy)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（比如100MB）
        assert memory_increase < 100 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__])