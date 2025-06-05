# 开发文档

## 项目概述

A股量化选股推荐系统是一个基于Web的量化投资平台，提供每日买入和卖出策略推荐。系统采用前后端分离架构，支持多种数据源和策略模块。

## 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **图表**: ECharts
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Vite

### 后端
- **框架**: FastAPI + Python 3.11
- **数据库**: PostgreSQL
- **缓存**: Redis
- **ORM**: SQLAlchemy
- **异步**: asyncio
- **API文档**: Swagger/OpenAPI

### 数据源
- **Tushare**: 专业金融数据接口
- **新浪财经**: 实时行情数据
- **东方财富**: 市场数据补充
- **CSV文件**: 本地数据备用

## 项目结构

```
stock/
├── frontend/                 # 前端Vue应用
│   ├── src/
│   │   ├── components/       # 可复用组件
│   │   ├── views/           # 页面组件
│   │   ├── api/             # API接口封装
│   │   ├── stores/          # Pinia状态管理
│   │   ├── router/          # 路由配置
│   │   └── utils/           # 工具函数
│   ├── package.json         # 前端依赖
│   └── Dockerfile           # 前端容器配置
├── backend/                  # 后端FastAPI应用
│   ├── app/
│   │   ├── api/             # API路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   └── main.py          # 应用入口
│   └── Dockerfile           # 后端容器配置
├── data/                     # 数据模块
│   ├── sources/             # 数据源适配器
│   ├── cache.py             # 数据缓存
│   └── manager.py           # 数据管理器
├── strategies/               # 策略模块
│   ├── base.py              # 策略基类
│   ├── technical.py         # 技术面策略
│   └── fundamental.py       # 基本面策略
├── ai/                       # AI模块
│   ├── model_manager.py     # 模型管理
│   ├── nlp_processor.py     # 自然语言处理
│   └── recommendation_generator.py # 推荐生成
├── config/                   # 配置文件
│   ├── settings.py          # 应用配置
│   ├── database.py          # 数据库配置
│   └── api_keys.py.example  # API密钥示例
├── scripts/                  # 脚本文件
│   └── init.sql             # 数据库初始化
├── docs/                     # 文档
├── requirements.txt          # Python依赖
├── docker-compose.yml        # Docker编排
├── start.sh                  # 启动脚本
└── stop.sh                   # 停止脚本
```

## 开发环境搭建

### 1. 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 6+

### 2. 克隆项目
```bash
git clone <repository-url>
cd stock
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 4. 安装依赖
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 5. 数据库初始化
```bash
# 创建数据库
psql -U postgres -c "CREATE DATABASE stock_db;"

# 执行初始化脚本
psql -U postgres -d stock_db -f scripts/init.sql
```

### 6. 启动服务
```bash
# 使用启动脚本
./start.sh

# 或手动启动
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
```

## API接口文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口

#### 推荐接口
- `GET /api/v1/recommendations/buy` - 获取买入推荐
- `GET /api/v1/recommendations/sell` - 获取卖出推荐
- `POST /api/v1/recommendations/generate` - 生成推荐

#### 股票接口
- `GET /api/v1/stocks` - 获取股票列表
- `GET /api/v1/stocks/{code}` - 获取股票详情
- `GET /api/v1/stocks/{code}/prices` - 获取股票价格数据

#### 策略接口
- `GET /api/v1/strategies` - 获取策略列表
- `POST /api/v1/strategies/{id}/execute` - 执行策略
- `GET /api/v1/strategies/{id}/backtest` - 策略回测

## 数据源配置

### Tushare配置
1. 注册Tushare账号: https://tushare.pro
2. 获取Token
3. 在.env文件中设置: `TUSHARE_TOKEN=your_token`

### 其他数据源
- 新浪财经: 无需配置，直接使用
- 东方财富: 无需配置，直接使用
- CSV数据: 将CSV文件放入 `data/csv/` 目录

## 策略开发

### 1. 创建新策略
```python
from strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    async def execute(self, stock_codes):
        # 实现策略逻辑
        pass
    
    def get_description(self):
        return "我的策略描述"
    
    def get_parameters_schema(self):
        return {
            "param1": {
                "type": float,
                "default": 0.5,
                "min": 0,
                "max": 1
            }
        }
```

### 2. 注册策略
在 `strategies/__init__.py` 中注册新策略。

### 3. 策略测试
```python
# 创建测试文件
# tests/test_my_strategy.py
```

## 前端开发

### 1. 组件开发
- 使用Vue 3 Composition API
- 遵循Element Plus设计规范
- 使用TypeScript类型检查

### 2. 状态管理
```typescript
// stores/example.ts
import { defineStore } from 'pinia'

export const useExampleStore = defineStore('example', {
  state: () => ({
    // 状态定义
  }),
  actions: {
    // 动作定义
  }
})
```

### 3. API调用
```typescript
// api/example.ts
import api from './index'

export const getExample = () => {
  return api.get('/api/v1/example')
}
```

## 部署

### Docker部署
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 生产环境配置
1. 修改 `.env` 文件中的生产环境配置
2. 设置安全的SECRET_KEY
3. 配置HTTPS
4. 设置防火墙规则
5. 配置监控和日志

## 测试

### 后端测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_strategies.py

# 生成覆盖率报告
pytest --cov=app
```

### 前端测试
```bash
# 运行单元测试
npm run test

# 运行E2E测试
npm run test:e2e
```

## 常见问题

### 1. 数据库连接失败
- 检查PostgreSQL服务是否启动
- 验证数据库连接字符串
- 确认数据库用户权限

### 2. API请求失败
- 检查后端服务是否启动
- 验证API地址配置
- 查看网络连接状态

### 3. 数据获取失败
- 检查数据源API配置
- 验证API密钥有效性
- 查看请求频率限制

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License