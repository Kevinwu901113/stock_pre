# 测试和部署指南

本文档提供了股票推荐系统的完整测试和部署方案，包括API测试、Docker部署、日志记录和流程验证。

## 一、API接口测试

### 1.1 Postman测试集合

#### 环境变量设置
```json
{
  "base_url": "http://localhost:8000",
  "api_version": "v1"
}
```

#### 核心接口测试用例

**1. 获取买入推荐**
```
GET {{base_url}}/api/{{api_version}}/recommendations/buy
Query Params:
- limit: 10
- date: 2024-01-15
- min_confidence: 0.7

预期响应结构:
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "uuid",
      "stockCode": "000001",
      "stockName": "平安银行",
      "currentPrice": 12.50,
      "targetPrice": 14.00,
      "stopLoss": 11.50,
      "confidence": 0.85,
      "reason": "技术指标显示突破关键阻力位",
      "strategyName": "MA均线策略",
      "createdAt": "2024-01-15T09:30:00Z"
    }
  ]
}
```

**2. 获取卖出推荐**
```
GET {{base_url}}/api/{{api_version}}/recommendations/sell
Query Params:
- limit: 10
- date: 2024-01-15

预期响应结构: 同买入推荐
```

**3. 生成推荐**
```
POST {{base_url}}/api/{{api_version}}/recommendations/generate
Content-Type: application/json

{
  "stockCodes": ["000001", "600036"],
  "strategies": ["ma_strategy", "rsi_strategy"],
  "parameters": {
    "minConfidence": 0.7
  }
}

预期响应:
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "uuid",
    "status": "processing",
    "message": "推荐生成任务已提交"
  }
}
```

**4. 股票搜索**
```
GET {{base_url}}/api/{{api_version}}/stocks/search
Query Params:
- keyword: 平安
- limit: 10

预期响应:
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "code": "000001",
      "name": "平安银行",
      "market": "A",
      "industry": "银行",
      "currentPrice": 12.50,
      "changePercent": 2.5
    }
  ]
}
```

**5. K线数据**
```
GET {{base_url}}/api/{{api_version}}/stocks/000001/kline
Query Params:
- period: daily
- start_date: 2024-01-01
- end_date: 2024-01-15

预期响应:
{
  "code": 200,
  "message": "success",
  "data": {
    "stockCode": "000001",
    "stockName": "平安银行",
    "klineData": [
      {
        "date": "2024-01-15",
        "open": 12.20,
        "high": 12.80,
        "low": 12.10,
        "close": 12.50,
        "volume": 1000000,
        "amount": 12500000.0
      }
    ]
  }
}
```

### 1.2 自动化测试脚本

创建 `tests/postman_tests.py`：
```python
import requests
import json
from datetime import datetime

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_version = "v1"
        
    def test_buy_recommendations(self):
        """测试买入推荐接口"""
        url = f"{self.base_url}/api/{self.api_version}/recommendations/buy"
        params = {"limit": 10, "min_confidence": 0.7}
        
        response = requests.get(url, params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert "code" in data
        assert "data" in data
        assert data["code"] == 200
        
        print("✅ 买入推荐接口测试通过")
        return data
    
    def test_stock_search(self):
        """测试股票搜索接口"""
        url = f"{self.base_url}/api/{self.api_version}/stocks/search"
        params = {"keyword": "平安", "limit": 10}
        
        response = requests.get(url, params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]) > 0
        
        print("✅ 股票搜索接口测试通过")
        return data
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始API接口测试...")
        
        try:
            self.test_buy_recommendations()
            self.test_stock_search()
            print("\n🎉 所有API测试通过！")
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
```

## 二、Docker Compose部署

### 2.1 优化的docker-compose.yml

```yaml
version: '3.8'

services:
  # 后端API服务
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/stock_db
      - REDIS_URL=redis://redis:6379/0
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost:3000,http://localhost:8087
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./strategies:/app/strategies
      - ./config:/app/config
      - ./logs:/app/logs
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - stock-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
      - NODE_ENV=development
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0 --port 3000
    networks:
      - stock-network
    depends_on:
      - backend

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=stock_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - stock-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - stock-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Nginx反向代理（生产环境）
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - stock-network
    profiles:
      - production

volumes:
  postgres_data:
  redis_data:

networks:
  stock-network:
    driver: bridge
```

### 2.2 Nginx配置（生产环境）

创建 `nginx/nginx.conf`：
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    # 前端服务
    server {
        listen 80;
        server_name localhost;
        
        # 前端静态资源
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API接口
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS设置
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            
            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }
        
        # API文档
        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### 2.3 部署脚本

创建 `scripts/deploy.sh`：
```bash
#!/bin/bash

set -e

echo "🚀 开始部署股票推荐系统..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
mkdir -p logs data/csv data/cache

# 停止现有服务
echo "📦 停止现有服务..."
docker-compose down

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 测试API连接
echo "🧪 测试API连接..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端API服务正常"
else
    echo "❌ 后端API服务异常"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

echo "🎉 部署完成！"
echo "📊 前端地址: http://localhost:3000"
echo "📡 API文档: http://localhost:8000/docs"
echo "📈 API地址: http://localhost:8000/api/v1"
```

## 三、日志记录系统

### 3.1 增强的日志配置

创建 `backend/app/core/logging.py`：
```python
import os
import sys
from loguru import logger
from datetime import datetime
from config.settings import settings

def setup_logging():
    """设置日志配置"""
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # 确保日志目录存在
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # 应用日志文件
    logger.add(
        os.path.join(settings.LOG_DIR, "app.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # 推荐生成专用日志
    logger.add(
        os.path.join(settings.LOG_DIR, "recommendations.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        rotation="1 day",
        retention="90 days",
        filter=lambda record: "recommendation" in record["name"].lower()
    )
    
    # 错误日志文件
    logger.add(
        os.path.join(settings.LOG_DIR, "errors.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation="1 week",
        retention="12 weeks"
    )
    
    return logger

class RecommendationLogger:
    """推荐生成专用日志记录器"""
    
    def __init__(self):
        self.logger = logger.bind(name="recommendation")
    
    def log_generation_start(self, task_id: str, stock_codes: list, strategies: list):
        """记录推荐生成开始"""
        self.logger.info(
            f"推荐生成开始 - 任务ID: {task_id} | "
            f"股票数量: {len(stock_codes)} | "
            f"策略: {', '.join(strategies)} | "
            f"开始时间: {datetime.now()}"
        )
    
    def log_generation_complete(self, task_id: str, recommendations_count: int, duration: float):
        """记录推荐生成完成"""
        self.logger.info(
            f"推荐生成完成 - 任务ID: {task_id} | "
            f"生成数量: {recommendations_count} | "
            f"耗时: {duration:.2f}秒 | "
            f"完成时间: {datetime.now()}"
        )
    
    def log_generation_error(self, task_id: str, error: str):
        """记录推荐生成错误"""
        self.logger.error(
            f"推荐生成失败 - 任务ID: {task_id} | "
            f"错误信息: {error} | "
            f"失败时间: {datetime.now()}"
        )
    
    def log_strategy_execution(self, strategy_name: str, stock_code: str, result: dict):
        """记录策略执行结果"""
        self.logger.info(
            f"策略执行 - 策略: {strategy_name} | "
            f"股票: {stock_code} | "
            f"信号: {result.get('signal', 'none')} | "
            f"置信度: {result.get('confidence', 0):.3f}"
        )
```

### 3.2 推荐服务日志增强

更新 `backend/app/services/recommendation_service.py`：
```python
from app.core.logging import RecommendationLogger
import time
import uuid

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.rec_logger = RecommendationLogger()
    
    async def generate_recommendations(self, stock_codes: list, strategies: list, parameters: dict):
        """生成推荐（增强日志记录）"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 记录开始
        self.rec_logger.log_generation_start(task_id, stock_codes, strategies)
        
        try:
            recommendations = []
            
            for stock_code in stock_codes:
                for strategy_name in strategies:
                    try:
                        # 执行策略
                        result = await self._execute_strategy(strategy_name, stock_code, parameters)
                        
                        # 记录策略执行结果
                        self.rec_logger.log_strategy_execution(strategy_name, stock_code, result)
                        
                        if result.get('signal') in ['buy', 'sell']:
                            recommendations.append(result)
                            
                    except Exception as e:
                        self.rec_logger.log_generation_error(task_id, f"策略执行失败: {strategy_name} - {stock_code} - {str(e)}")
            
            # 记录完成
            duration = time.time() - start_time
            self.rec_logger.log_generation_complete(task_id, len(recommendations), duration)
            
            return {
                "task_id": task_id,
                "recommendations": recommendations,
                "duration": duration
            }
            
        except Exception as e:
            self.rec_logger.log_generation_error(task_id, str(e))
            raise
```

## 四、完整流程验证

### 4.1 端到端测试脚本

创建 `scripts/e2e_test.py`：
```python
#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime, timedelta

class E2ETestSuite:
    """端到端测试套件"""
    
    def __init__(self, backend_url="http://localhost:8000", frontend_url="http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_stocks = ["000001", "600036", "000002"]  # 测试股票代码
        
    def test_backend_health(self):
        """测试后端健康状态"""
        print("🔍 测试后端健康状态...")
        response = requests.get(f"{self.backend_url}/health")
        assert response.status_code == 200
        print("✅ 后端服务正常")
        
    def test_frontend_access(self):
        """测试前端访问"""
        print("🔍 测试前端访问...")
        response = requests.get(self.frontend_url)
        assert response.status_code == 200
        print("✅ 前端服务正常")
        
    def test_stock_data_preparation(self):
        """测试股票数据准备"""
        print("🔍 测试股票数据准备...")
        
        # 检查股票是否存在
        for stock_code in self.test_stocks:
            response = requests.get(f"{self.backend_url}/api/v1/stocks/{stock_code}")
            if response.status_code == 404:
                # 如果股票不存在，添加测试数据
                self._add_test_stock_data(stock_code)
                
        print("✅ 股票数据准备完成")
        
    def test_recommendation_generation(self):
        """测试推荐生成流程"""
        print("🔍 测试推荐生成流程...")
        
        # 生成推荐
        payload = {
            "stockCodes": self.test_stocks,
            "strategies": ["ma_strategy", "rsi_strategy"],
            "parameters": {
                "minConfidence": 0.6
            }
        }
        
        response = requests.post(
            f"{self.backend_url}/api/v1/recommendations/generate",
            json=payload
        )
        
        assert response.status_code == 200
        result = response.json()
        task_id = result["data"]["taskId"]
        
        print(f"✅ 推荐生成任务提交成功，任务ID: {task_id}")
        
        # 等待生成完成
        time.sleep(5)
        
        return task_id
        
    def test_recommendation_retrieval(self):
        """测试推荐获取"""
        print("🔍 测试推荐获取...")
        
        # 获取买入推荐
        response = requests.get(f"{self.backend_url}/api/v1/recommendations/buy?limit=10")
        assert response.status_code == 200
        
        buy_recommendations = response.json()["data"]
        print(f"✅ 获取到 {len(buy_recommendations)} 条买入推荐")
        
        # 获取卖出推荐
        response = requests.get(f"{self.backend_url}/api/v1/recommendations/sell?limit=10")
        assert response.status_code == 200
        
        sell_recommendations = response.json()["data"]
        print(f"✅ 获取到 {len(sell_recommendations)} 条卖出推荐")
        
        return buy_recommendations, sell_recommendations
        
    def test_frontend_display(self, recommendations):
        """测试前端显示（模拟）"""
        print("🔍 测试前端显示...")
        
        # 这里可以添加Selenium测试或API调用测试
        # 暂时通过检查推荐数据结构来验证
        
        for rec in recommendations[:3]:  # 检查前3条推荐
            required_fields = [
                'stockCode', 'stockName', 'currentPrice', 
                'targetPrice', 'confidence', 'reason'
            ]
            
            for field in required_fields:
                assert field in rec, f"推荐数据缺少字段: {field}"
                
        print("✅ 推荐数据结构验证通过")
        
    def _add_test_stock_data(self, stock_code):
        """添加测试股票数据"""
        stock_data = {
            "code": stock_code,
            "name": f"测试股票{stock_code}",
            "market": "A",
            "industry": "测试行业"
        }
        
        response = requests.post(
            f"{self.backend_url}/api/v1/stocks",
            json=stock_data
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ 添加测试股票: {stock_code}")
        
    def run_full_test(self):
        """运行完整测试流程"""
        print("🚀 开始端到端测试...\n")
        
        try:
            # 1. 测试服务健康状态
            self.test_backend_health()
            self.test_frontend_access()
            
            # 2. 准备测试数据
            self.test_stock_data_preparation()
            
            # 3. 测试推荐生成
            task_id = self.test_recommendation_generation()
            
            # 4. 测试推荐获取
            buy_recs, sell_recs = self.test_recommendation_retrieval()
            
            # 5. 测试前端显示
            if buy_recs:
                self.test_frontend_display(buy_recs)
            
            print("\n🎉 端到端测试全部通过！")
            
            # 输出测试报告
            self._generate_test_report(task_id, buy_recs, sell_recs)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            raise
            
    def _generate_test_report(self, task_id, buy_recs, sell_recs):
        """生成测试报告"""
        report = {
            "测试时间": datetime.now().isoformat(),
            "任务ID": task_id,
            "买入推荐数量": len(buy_recs),
            "卖出推荐数量": len(sell_recs),
            "测试股票": self.test_stocks,
            "测试结果": "通过"
        }
        
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📊 测试报告已保存到 test_report.json")
        print(f"📈 买入推荐: {len(buy_recs)} 条")
        print(f"📉 卖出推荐: {len(sell_recs)} 条")

if __name__ == "__main__":
    tester = E2ETestSuite()
    tester.run_full_test()
```

### 4.2 数据准备脚本

创建 `scripts/prepare_test_data.py`：
```python
#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_test_stock_data():
    """生成测试股票数据"""
    
    # 测试股票列表
    test_stocks = [
        {"code": "000001", "name": "平安银行", "industry": "银行"},
        {"code": "600036", "name": "招商银行", "industry": "银行"},
        {"code": "000002", "name": "万科A", "industry": "房地产"},
        {"code": "600519", "name": "贵州茅台", "industry": "白酒"},
        {"code": "000858", "name": "五粮液", "industry": "白酒"}
    ]
    
    # 确保CSV目录存在
    csv_dir = "data/csv"
    os.makedirs(csv_dir, exist_ok=True)
    
    # 生成股票基础信息
    stocks_df = pd.DataFrame(test_stocks)
    stocks_df.to_csv(f"{csv_dir}/stocks.csv", index=False, encoding="utf-8")
    
    # 生成价格数据
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)  # 一年的数据
    
    all_price_data = []
    
    for stock in test_stocks:
        stock_code = stock["code"]
        
        # 生成模拟价格数据
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 模拟价格走势
        base_price = np.random.uniform(10, 100)  # 基础价格
        price_trend = np.cumsum(np.random.normal(0, 0.02, len(dates)))  # 价格趋势
        
        for i, date in enumerate(dates):
            # 跳过周末
            if date.weekday() >= 5:
                continue
                
            daily_change = np.random.normal(0, 0.03)  # 日内波动
            
            open_price = base_price * (1 + price_trend[i] + daily_change)
            close_price = open_price * (1 + np.random.normal(0, 0.02))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            volume = int(np.random.uniform(1000000, 10000000))  # 成交量
            amount = volume * close_price  # 成交额
            
            all_price_data.append({
                "stock_code": stock_code,
                "date": date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume,
                "amount": round(amount, 2),
                "turnover_rate": round(np.random.uniform(0.5, 5.0), 2)
            })
    
    # 保存价格数据
    price_df = pd.DataFrame(all_price_data)
    price_df.to_csv(f"{csv_dir}/stock_prices.csv", index=False, encoding="utf-8")
    
    print(f"✅ 测试数据生成完成:")
    print(f"   - 股票数量: {len(test_stocks)}")
    print(f"   - 价格数据: {len(all_price_data)} 条")
    print(f"   - 数据目录: {csv_dir}")
    
    return test_stocks, all_price_data

if __name__ == "__main__":
    generate_test_stock_data()
```

## 五、使用指南

### 5.1 快速部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd stock

# 2. 准备测试数据
python3 scripts/prepare_test_data.py

# 3. 部署服务
bash scripts/deploy.sh

# 4. 运行端到端测试
python3 scripts/e2e_test.py

# 5. 运行API测试
python3 tests/postman_tests.py
```

### 5.2 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看推荐生成日志
tail -f logs/recommendations.log

# 查看错误日志
tail -f logs/errors.log

# 查看Docker容器日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5.3 监控和维护

```bash
# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 查看资源使用
docker stats

# 清理日志（保留最近30天）
find logs/ -name "*.log" -mtime +30 -delete
```

## 六、故障排除

### 6.1 常见问题

**问题1: 端口冲突**
```bash
# 检查端口占用
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# 修改docker-compose.yml中的端口映射
```

**问题2: 数据库连接失败**
```bash
# 检查PostgreSQL状态
docker-compose logs postgres

# 重置数据库
docker-compose down
docker volume rm stock_postgres_data
docker-compose up -d
```

**问题3: 前端无法访问后端API**
```bash
# 检查CORS配置
# 确认backend/app/main.py中的CORS设置
# 检查nginx配置（如果使用）
```

### 6.2 性能优化

1. **数据库优化**
   - 添加适当的索引
   - 定期清理历史数据
   - 使用连接池

2. **缓存优化**
   - 启用Redis缓存
   - 设置合适的缓存过期时间
   - 缓存热点数据

3. **API优化**
   - 实现分页查询
   - 添加请求限流
   - 优化数据库查询

通过以上完整的测试和部署方案，可以确保股票推荐系统的稳定运行和持续监控。