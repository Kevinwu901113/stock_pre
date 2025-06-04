# 🚀 A股量化推荐系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📖 项目简介

本项目是一个基于Web的A股市场量化选股推荐系统，旨在通过技术分析和量化策略为投资者提供每日的买入和卖出建议。系统采用前后端分离架构，提供实时数据分析、策略回测和可视化展示功能。

### ✨ 核心功能
- **🎯 尾盘推荐买入策略**：基于技术指标分析，在收盘前推荐潜力股票
- **📈 早盘推荐卖出策略**：基于隔夜表现和开盘情况，推荐卖出时机
- **📊 可视化展示**：直观的图表和数据展示，支持历史回测和策略对比
- **🔗 多数据源支持**：集成tushare、AKShare、yfinance等多个数据源
- **🤖 AI智能分析**：集成AI模块提供推荐理由和市场分析
- **⏰ 定时任务**：自动化数据更新和策略执行
- **💾 缓存机制**：Redis缓存提升系统响应速度
- **📝 完整日志**：详细的操作日志和异常处理

## 项目结构

```
stock/
├── backend/           # 后端服务（FastAPI）
│   ├── app/
│   │   ├── ai/        # AI模块（推荐解释、市场分析）
│   │   ├── api/       # API路由
│   │   ├── core/      # 核心配置（日志、异常、缓存）
│   │   ├── data/      # 数据模块
│   │   ├── models/    # 数据模型
│   │   ├── scheduler/ # 定时任务
│   │   ├── services/  # 业务逻辑
│   │   └── strategies/ # 策略模块
│   ├── logs/          # 日志文件目录
│   ├── main.py        # 应用入口
│   └── requirements.txt
├── frontend/          # 前端应用（React + Vite）
│   ├── src/
│   │   ├── components/ # 组件
│   │   ├── hooks/     # React Hooks
│   │   ├── pages/     # 页面
│   │   ├── services/  # API服务
│   │   ├── store/     # 状态管理
│   │   ├── styles/    # 样式文件
│   │   ├── types/     # TypeScript类型
│   │   └── utils/     # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── data/              # 数据文件
├── docs/              # 文档
├── scripts/           # 脚本文件
├── tests/             # 测试文件
└── README.md
```

## 🔧 技术栈

## 📚 API文档

### 主要接口

#### 获取推荐股票
```http
GET /api/recommend?strategy=buy&limit=10
```

#### 获取股票历史数据
```http
GET /api/data/stock/{stock_code}?period=1d&start_date=2024-01-01
```

#### 获取策略回测结果
```http
GET /api/backtest/{strategy_name}?start_date=2024-01-01&end_date=2024-12-31
```

#### 获取市场概况
```http
GET /api/market/overview
```

更多详细API文档请访问: http://localhost:8000/docs

## ⚙️ 配置说明

### 环境变量配置

主要配置项说明（详见`.env.example`）：

```bash
# 基础配置
DEBUG=true                    # 调试模式
HOST=0.0.0.0                 # 服务器地址
PORT=8000                    # 服务器端口

# 数据源配置
TUSHARE_TOKEN=your_token     # Tushare API Token
AKSHARE_ENABLED=true         # 启用AKShare数据源

# 缓存配置
REDIS_HOST=localhost         # Redis服务器地址
REDIS_PORT=6379             # Redis端口
REDIS_DB=0                  # Redis数据库

# 策略配置
STRATEGY_ENABLED=true        # 启用策略模块
SCHEDULER_ENABLED=true       # 启用定时任务

# AI配置
AI_ENABLED=false            # 启用AI模块
OPENAI_API_KEY=your_key     # OpenAI API Key
```

### 策略参数配置

在`backend/app/strategies/config.py`中可以调整策略参数：

```python
# 尾盘买入策略参数
BUY_STRATEGY_CONFIG = {
    "min_volume": 1000000,      # 最小成交量
    "max_pe_ratio": 30,        # 最大市盈率
    "min_market_cap": 50,      # 最小市值(亿)
    "technical_indicators": {   # 技术指标参数
        "ma_period": 5,
        "rsi_period": 14,
        "volume_ratio": 1.5
    }
}
```

## 🔄 定时任务

系统支持以下定时任务：

- **数据更新**: 每日15:30更新股票数据
- **尾盘推荐**: 每日14:30生成买入推荐
- **早盘推荐**: 每日09:15生成卖出推荐
- **策略回测**: 每周末进行策略效果评估

## 🧪 测试

### 后端测试
```bash
cd backend
pytest tests/ -v
```

### 前端测试
```bash
cd frontend
npm run test
```

## 📈 性能优化

- **缓存策略**: 使用Redis缓存热点数据
- **数据分页**: API支持分页查询
- **异步处理**: 使用FastAPI异步特性
- **CDN加速**: 静态资源CDN分发

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 代码规范

- Python代码使用`black`格式化
- TypeScript代码使用`prettier`格式化
- 提交信息遵循[Conventional Commits](https://conventionalcommits.org/)规范

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。使用本系统进行实际投资造成的任何损失，开发者不承担责任。

## 📞 联系方式

- 项目主页: https://github.com/yourusername/stock
- 问题反馈: https://github.com/yourusername/stock/issues
- 邮箱: your.email@example.com

## 🙏 致谢

感谢以下开源项目和数据提供商：

- [Tushare](https://tushare.pro/) - 金融数据接口
- [AKShare](https://github.com/akfamily/akshare) - 金融数据工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [React](https://reactjs.org/) - 用户界面库
- [Ant Design](https://ant.design/) - 企业级UI设计语言
- [ECharts](https://echarts.apache.org/) - 数据可视化图表库

### 后端
- **FastAPI**: 高性能Web框架
- **Python 3.8+**: 主要开发语言
- **Pandas**: 数据处理和分析
- **NumPy**: 数值计算
- **Tushare**: 金融数据接口
- **AKShare**: 备用数据源
- **APScheduler**: 定时任务调度
- **Loguru**: 日志管理
- **Redis**: 缓存支持（可选）
- **Pydantic**: 数据验证

### 前端
- **React 18**: 用户界面框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **TailwindCSS**: CSS框架
- **ECharts**: 图表库
- **Axios**: HTTP客户端
- **React Router**: 路由管理

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn
- Redis（可选，用于缓存）

### 1. 克隆项目
```bash
git clone <repository-url>
cd stock
```

### 2. 后端设置
```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，设置数据源API密钥等

# 启动后端服务
python main.py
```

后端服务将在 http://localhost:8000 启动

### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:3000 启动

### 4. 访问应用
打开浏览器访问 http://localhost:3000 即可使用系统

## 配置说明

### 环境变量配置

在 `backend` 目录下创建 `.env` 文件，配置以下参数：

```env
# 基础配置
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据源配置
TUSHARE_TOKEN=your_tushare_token_here
AKSHARE_ENABLED=true

# 缓存配置
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0
CACHE_EXPIRE_MINUTES=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# AI配置（可选）
AI_DEFAULT_PROVIDER=mock
AI_ENABLED_PROVIDERS=["mock"]
# OPENAI_API_KEY=your_openai_key
# CLAUDE_API_KEY=your_claude_key
```

### 数据源配置

#### Tushare（推荐）
1. 注册 [Tushare](https://tushare.pro/) 账号
2. 获取API Token
3. 在 `.env` 文件中设置 `TUSHARE_TOKEN`

#### AKShare（备用）
- 无需API密钥，默认启用
- 可通过 `AKSHARE_ENABLED=false` 禁用

### 缓存配置

#### 内存缓存（默认）
- 无需额外配置
- 适合单机部署

#### Redis缓存（推荐生产环境）
```bash
# 安装Redis
sudo apt-get install redis-server  # Ubuntu
brew install redis                 # macOS

# 启动Redis
redis-server

# 在.env中启用Redis
REDIS_ENABLED=true
```

## 功能特性

### 核心功能
- ✅ **多策略支持**: 支持多种量化策略的组合使用
- ✅ **实时数据**: 集成多个数据源，确保数据的准确性和及时性
- ✅ **智能缓存**: 支持内存和Redis缓存，提升系统性能
- ✅ **异常处理**: 完善的异常处理和日志记录机制
- ✅ **AI集成**: 预留AI接口，支持推荐理由解释和市场分析
- ✅ **可视化**: 丰富的图表展示和历史数据回测

### 策略说明

#### 尾盘买入策略
- **技术指标**: 5分钟均线突破
- **成交量确认**: 成交量放大验证
- **过滤条件**: 市值、换手率等基本面过滤
- **执行时间**: 每日14:50执行

#### 早盘卖出策略
- **模式识别**: 高开高走模式检测
- **止盈止损**: 动态止盈止损设置
- **风险控制**: 多层风险控制机制
- **执行时间**: 每日09:35执行

### API接口

#### 主要接口
- `GET /api/recommend` - 获取推荐列表
- `GET /api/data/stock/{code}` - 获取股票历史数据
- `GET /api/strategy/status` - 获取策略运行状态
- `POST /api/strategy/run` - 手动执行策略
- `GET /api/cache/status` - 获取缓存状态

#### 接口文档
启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档

## 使用指南

### 基本使用流程

1. **启动系统**: 按照快速开始指南启动前后端服务
2. **查看推荐**: 在首页查看当日推荐股票列表
3. **详细分析**: 点击股票查看详细的技术分析图表
4. **历史回测**: 在历史页面查看策略的历史表现
5. **策略配置**: 在设置页面调整策略参数

### 定时任务

系统支持自动定时执行策略：
- **尾盘策略**: 每个交易日14:50自动执行
- **早盘策略**: 每个交易日09:35自动执行
- **数据更新**: 定期更新股票基础数据

### 监控和日志

- **日志文件**: 查看 `backend/logs/` 目录下的日志文件
- **系统状态**: 通过API接口监控系统运行状态
- **缓存监控**: 查看缓存命中率和使用情况

## 开发指南

### 添加新策略

1. 在 `backend/app/strategies/` 目录下创建新的策略文件
2. 继承 `BaseStrategy` 类并实现必要方法
3. 在策略配置中注册新策略
4. 编写相应的测试用例

### 扩展数据源

1. 在 `backend/app/data/` 目录下创建新的数据源客户端
2. 实现统一的数据接口
3. 在配置文件中添加数据源配置
4. 更新数据服务以支持新数据源

### 自定义AI提供商

1. 实现 `AIInterface` 接口
2. 在 `AIFactory` 中注册新的提供商
3. 配置相应的API密钥和参数

## 部署指南

### Docker部署（推荐）

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 生产环境部署

1. **后端部署**:
   - 使用 Gunicorn 或 Uvicorn 作为WSGI服务器
   - 配置Nginx作为反向代理
   - 设置Redis作为缓存服务

2. **前端部署**:
   - 构建生产版本: `npm run build`
   - 部署到CDN或静态文件服务器

3. **数据库**:
   - 可选择SQLite（开发）或PostgreSQL（生产）
   - 配置数据备份策略

## 开发计划

详见 [project_plan.md](./project_plan.md)

## 故障排除

### 常见问题

1. **数据获取失败**
   - 检查网络连接
   - 验证API密钥是否正确
   - 查看日志文件获取详细错误信息

2. **缓存问题**
   - 检查Redis服务是否正常运行
   - 清空缓存: 访问 `/api/cache/clear`

3. **策略执行异常**
   - 查看策略日志
   - 检查数据完整性
   - 验证策略参数配置

### 性能优化

- 启用Redis缓存
- 调整缓存过期时间
- 优化数据库查询
- 使用CDN加速前端资源

## 贡献指南

我们欢迎任何形式的贡献！

### 如何贡献

1. **Fork** 本项目
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 提交 **Pull Request**

### 代码规范

- **Python**: 遵循PEP 8规范
- **TypeScript**: 使用ESLint和Prettier
- **提交信息**: 使用清晰的提交信息
- **测试**: 为新功能添加相应测试

### 报告问题

如果发现bug或有功能建议，请在GitHub Issues中提交，包含：
- 详细的问题描述
- 复现步骤
- 系统环境信息
- 相关日志信息

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 免责声明

⚠️ **重要提示**: 本系统仅供学习和研究使用，不构成任何投资建议。

- 所有推荐结果仅基于历史数据和技术分析
- 股票投资存在风险，可能导致本金损失
- 使用本系统进行投资决策的风险由用户自行承担
- 开发者不对任何投资损失承担责任

**投资有风险，入市需谨慎！**

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: [your-email@example.com]

---

如果这个项目对您有帮助，请给我们一个 ⭐ Star！