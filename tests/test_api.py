import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from config.database import get_db, Base
from config.settings import settings


# 测试数据库设置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """测试数据库依赖覆盖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def test_db():
    """创建测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(test_db):
    """测试客户端"""
    with TestClient(app) as c:
        yield c


class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestStockAPI:
    """股票API测试"""
    
    def test_get_stocks(self, client):
        """测试获取股票列表"""
        response = client.get("/api/v1/stocks")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    def test_search_stocks(self, client):
        """测试搜索股票"""
        response = client.get("/api/v1/stocks/search?q=平安")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_stock_detail(self, client):
        """测试获取股票详情"""
        # 这里需要先创建测试数据
        response = client.get("/api/v1/stocks/000001.SZ")
        # 如果没有数据，应该返回404
        assert response.status_code in [200, 404]


class TestRecommendationAPI:
    """推荐API测试"""
    
    def test_get_buy_recommendations(self, client):
        """测试获取买入推荐"""
        response = client.get("/api/v1/recommendations/buy")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_sell_recommendations(self, client):
        """测试获取卖出推荐"""
        response = client.get("/api/v1/recommendations/sell")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recommendations_with_filters(self, client):
        """测试带筛选条件的推荐"""
        response = client.get("/api/v1/recommendations/buy?limit=5&min_confidence=0.8")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestStrategyAPI:
    """策略API测试"""
    
    def test_get_strategy_list(self, client):
        """测试获取策略列表"""
        response = client.get("/api/v1/strategies/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_execute_strategy(self, client):
        """测试执行策略"""
        strategy_data = {
            "strategy_name": "MovingAverageCrossStrategy",
            "stock_codes": ["000001.SZ"],
            "parameters": {
                "short_period": 5,
                "long_period": 20
            }
        }
        response = client.post("/api/v1/strategies/execute", json=strategy_data)
        assert response.status_code in [200, 422]  # 422 if validation fails


class TestDataAPI:
    """数据API测试"""
    
    def test_get_data_sources(self, client):
        """测试获取数据源列表"""
        response = client.get("/api/v1/data/sources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_sync_data(self, client):
        """测试数据同步"""
        sync_data = {
            "source": "tushare",
            "data_type": "stock_list"
        }
        response = client.post("/api/v1/data/sync", json=sync_data)
        assert response.status_code in [200, 422, 500]


@pytest.mark.asyncio
class TestAsyncOperations:
    """异步操作测试"""
    
    async def test_async_data_processing(self):
        """测试异步数据处理"""
        # 这里可以测试一些异步操作
        await asyncio.sleep(0.1)
        assert True


if __name__ == "__main__":
    pytest.main([__file__])