# A股推荐算法系统

一个基于多因子模型的A股股票推荐系统，能够每日自动运行，在14:45输出买入推荐，在次日9:45给出卖出建议。

## 🚀 功能特性

- **多因子评分模型**：基于动量、成交量、资金流向、技术指标、市场情绪等多个维度进行综合评分
- **自动化运行**：支持定时任务，每日自动执行推荐和卖出分析
- **智能止盈止损**：自动监控持仓，提供止盈止损建议
- **灵活配置**：通过配置文件调整因子权重和系统参数
- **结果输出**：生成JSON格式的推荐结果，便于对接前端或API

## 📁 项目结构

```
stock/
├── data_fetcher.py         # 数据获取模块（AkShare等数据源）
├── feature_extractor.py    # 特征提取模块（技术指标、因子计算）
├── scoring_engine.py       # 打分引擎（多因子加权评分）
├── sell_decision.py        # 卖出决策模块（止盈止损逻辑）
├── main.py                 # 主程序入口
├── factor_config.yaml      # 因子配置文件
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明
└── result/                # 推荐结果输出目录
    ├── buy_YYYYMMDD.json  # 买入推荐结果
    └── sell_YYYYMMDD.json # 卖出建议结果
```

## 🛠️ 安装部署

### 1. 环境要求

- Python 3.8+
- 稳定的网络连接（用于获取股票数据）

### 2. 安装依赖

```bash
# 克隆或下载项目到本地
cd stock

# 安装依赖包
pip install -r requirements.txt
```

### 3. 配置系统

编辑 `factor_config.yaml` 文件，根据需要调整：
- 因子权重
- 推荐参数
- 止盈止损设置
- 数据源配置

## 🎯 使用方法

### 命令行使用

```bash
# 执行买入分析（推荐在14:45运行）
python main.py buy

# 执行卖出分析（推荐在9:45运行）
python main.py sell

# 执行完整分析（买入+卖出）
python main.py both

# 启动定时任务（自动化运行）
python main.py schedule
```

### 定时任务

系统支持自动定时执行：
- **买入分析**：每个交易日 14:45
- **卖出分析**：每个交易日 09:45

启动定时任务：
```bash
python main.py schedule
```

### 结果文件

系统会在 `result/` 目录下生成：

**买入推荐文件** (`buy_YYYYMMDD.json`)：
```json
{
  "date": "2024-01-15",
  "time": "14:45:00",
  "total_recommended": 20,
  "recommendations": [
    {
      "rank": 1,
      "stock_code": "000001",
      "stock_name": "平安银行",
      "current_price": 15.68,
      "change_pct": 2.1,
      "total_score": 85.2,
      "recommendation_reason": "动量表现良好; 资金流向积极; 市场情绪乐观",
      "score_breakdown": {
        "momentum": 25.5,
        "volume": 18.3,
        "capital_flow": 22.1,
        "sentiment": 15.8,
        "risk": 3.5
      }
    }
  ]
}
```

**卖出建议文件** (`sell_YYYYMMDD.json`)：
```json
{
  "summary": {
    "total_stocks": 10,
    "sell_count": 2,
    "reduce_count": 1,
    "hold_count": 7,
    "avg_return_rate": 1.25
  },
  "decisions": [
    {
      "stock_code": "000001",
      "stock_name": "平安银行",
      "action": "SELL",
      "sell_ratio": 1.0,
      "reason": "达到止盈条件，收益率3.2%",
      "buy_price": 15.68,
      "current_price": 16.18,
      "return_rate": 3.19,
      "urgency": "HIGH"
    }
  ]
}
```

## 📊 评分模型

### 默认因子权重

```yaml
# 动量因子 (35%)
momentum_5d: 0.10      # 5日动量
momentum_10d: 0.10     # 10日动量
momentum_20d: 0.10     # 20日动量
rsi: 0.05              # RSI指标

# 成交量因子 (20%)
volume_ratio: 0.08     # 成交量比率
volume_spike: 0.07     # 成交量突增
turnover_rate: 0.05    # 换手率

# 资金流向因子 (20%)
main_inflow_score: 0.10    # 主力资金净流入
large_inflow_score: 0.05   # 大单资金净流入
capital_strength: 0.05     # 综合资金强度

# 情绪因子 (17%)
news_sentiment_score: 0.08     # 新闻情绪
market_sentiment_score: 0.04   # 市场情绪
overall_sentiment: 0.05        # 综合情绪

# 技术指标 (8%)
macd: 0.05             # MACD
bollinger_position: 0.03   # 布林带位置

# 风险控制
volatility_20d: -0.05      # 波动率（负权重）
price_stability: 0.03      # 价格稳定性
```

### 综合评分公式

```
总分 = Σ(因子值 × 因子权重)
```

## ⚙️ 配置说明

### 推荐系统配置

- `top_recommendations`: 推荐股票数量（默认20只）
- `min_price`: 最低价格过滤（默认3元）
- `max_price`: 最高价格过滤（默认200元）
- `exclude_st`: 是否排除ST股票

### 卖出决策配置

- `profit_threshold`: 止盈阈值（默认3%）
- `loss_threshold`: 止损阈值（默认-3%）
- `max_hold_days`: 最大持有天数（默认5天）
- `technical_check`: 是否进行技术面检查

## 🔧 自定义开发

### 添加新因子

1. 在 `feature_extractor.py` 中添加新的因子计算方法
2. 在 `scoring_engine.py` 中添加对应的评分逻辑
3. 在 `factor_config.yaml` 中配置因子权重

### 修改数据源

在 `data_fetcher.py` 中修改数据获取逻辑，支持：
- 不同的数据API
- 本地数据文件
- 数据库连接

### 扩展卖出策略

在 `sell_decision.py` 中添加新的卖出条件：
- 技术指标信号
- 基本面变化
- 市场环境判断

## 📈 性能优化

### 数据缓存

- 启用Redis缓存减少API调用
- 本地文件缓存历史数据

### 并发处理

- 使用多线程获取股票数据
- 异步处理大量股票分析

### 算法优化

- 使用NumPy向量化计算
- 预计算常用技术指标

## 🚨 风险提示

1. **投资风险**：本系统仅供参考，不构成投资建议，投资有风险，入市需谨慎
2. **数据风险**：依赖第三方数据源，可能存在数据延迟或错误
3. **技术风险**：算法模型基于历史数据，不保证未来表现
4. **市场风险**：极端市场条件下系统可能失效

## 📝 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 实现多因子评分模型
- 支持自动化买入推荐和卖出决策
- 提供配置文件和定时任务功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至项目维护者

---

**免责声明**：本软件仅用于学习和研究目的，使用者应当遵守相关法律法规，并对使用本软件进行的任何投资决策承担全部责任。