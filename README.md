# A股量化选股推荐系统

一个基于Web的A股市场量化选股推荐系统，提供每日买入和卖出策略推荐。

## 项目特性

- 🎯 **智能推荐**: 每天尾盘推荐买入策略，早盘推荐卖出策略
- 📊 **可视化展示**: 股票列表、图表、趋势变化和策略理由
- 🔄 **多数据源**: 支持tushare、东方财富、新浪财经等API，以及本地CSV备用
- 🧩 **模块化设计**: 前后端分离，策略模块可插拔
- 🤖 **AI就绪**: 预留AI模型接口，支持智能分析
- 📈 **历史回测**: 支持历史查看与策略对比

## 项目架构

```
stock/
├── frontend/                 # 前端Vue.js应用
│   ├── src/
│   │   ├── components/       # 组件
│   │   ├── views/           # 页面
│   │   ├── api/             # API接口
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.js
├── backend/                  # 后端FastAPI应用
│   ├── app/
│   │   ├── api/             # API路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   └── main.py          # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── data/                     # 数据模块
│   ├── sources/             # 数据源适配器
│   ├── cache/               # 数据缓存
│   ├── csv/                 # 本地CSV数据
│   └── __init__.py
├── strategies/               # 策略模块
│   ├── technical/           # 技术面策略
│   ├── fundamental/         # 基本面策略
│   ├── sentiment/           # 情绪面策略
│   ├── base.py              # 策略基类
│   └── __init__.py
├── ai/                       # AI模块(预留)
│   ├── models/              # AI模型
│   ├── inference/           # 推理服务
│   └── __init__.py
├── config/                   # 配置文件
│   ├── settings.py          # 主配置
│   ├── database.py          # 数据库配置
│   └── api_keys.py.example  # API密钥示例
├── scripts/                  # 脚本工具
│   ├── start.sh             # 启动脚本
│   ├── setup.sh             # 环境设置
│   └── data_sync.py         # 数据同步
├── tests/                    # 测试文件
├── docs/                     # 文档
├── docker-compose.yml        # Docker编排
├── requirements.txt          # Python依赖
└── README.md                # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd stock

# 设置环境
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. 配置设置

```bash
# 复制配置文件
cp config/api_keys.py.example config/api_keys.py

# 编辑配置文件，填入API密钥
vim config/api_keys.py
```

### 3. 启动服务

```bash
# 使用Docker启动(推荐)
docker-compose up -d

# 或手动启动
./scripts/start.sh
```

### 4. 访问应用

- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 核心功能

### 数据模块

- **多数据源支持**: tushare、东方财富、新浪财经API
- **本地数据**: CSV文件备用方案
- **数据类型**: 日K线、分钟K线、资金流向、涨跌停、换手率、基本面数据
- **缓存机制**: Redis缓存，避免频繁API调用
- **定时同步**: 自动数据更新

### 策略模块

- **技术面策略**: 基于技术指标的选股策略
- **基本面策略**: 基于财务数据的价值投资策略
- **情绪面策略**: 基于市场情绪的短线策略
- **组合策略**: 多策略融合与权重配置
- **回测功能**: 历史数据验证策略效果

### 前端功能

- **推荐展示**: 买入/卖出推荐列表
- **图表分析**: K线图、技术指标图表
- **策略对比**: 不同策略效果对比
- **历史查看**: 历史推荐记录
- **实时更新**: WebSocket实时数据推送

## 开发指南

### 添加新策略

1. 在`strategies/`目录下创建策略文件
2. 继承`BaseStrategy`类
3. 实现`analyze()`和`recommend()`方法
4. 在配置文件中注册策略

### 添加新数据源

1. 在`data/sources/`目录下创建数据源适配器
2. 实现标准数据接口
3. 在配置文件中添加数据源配置

### API扩展

1. 在`backend/app/api/`目录下添加路由
2. 定义请求/响应模型
3. 实现业务逻辑
4. 更新API文档

## 技术栈

- **前端**: Vue.js 3 + TypeScript + Vite + Element Plus
- **后端**: FastAPI + Python 3.9+ + SQLAlchemy
- **数据库**: PostgreSQL + Redis
- **部署**: Docker + Docker Compose
- **监控**: Prometheus + Grafana

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！