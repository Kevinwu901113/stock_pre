# 股票推荐系统

一个模块化、可配置的股票推荐系统，支持多种投资策略和时间周期。

## 核心特性

### 🏗️ 模块化设计
- **数据获取模块** (`data_fetcher.py`): 负责从各种数据源获取股票数据
- **特征提取模块** (`feature_extractor.py`): 计算各种技术指标和因子
- **评分引擎模块** (`scoring_engine.py`): 对股票进行评分和排序
- **结果输出模块** (`result_writer.py`): 保存和导出推荐结果
- **卖出决策模块** (`sell_decision.py`): 分析持仓股票的卖出时机

### 🎯 多策略支持

#### 股票池策略
- **default**: 默认股票池，平衡风险和收益
- **conservative**: 保守策略，关注大盘蓝筹股
- **aggressive**: 激进策略，关注小盘成长股

#### 因子策略
- **default**: 默认因子权重，均衡配置
- **momentum_focused**: 动量导向，关注价格趋势
- **capital_flow_focused**: 资金流向导向，关注资金动向
- **conservative**: 保守因子配置，注重稳定性

#### 时间周期
- **short_term**: 短期策略 (5-10天)
- **medium_term**: 中期策略 (10-20天)
- **long_term**: 长期策略 (20-30天)

### ⚙️ 配置化管理
- 所有参数通过 `config.yaml` 统一管理
- 支持不同策略组合的灵活配置
- 无硬编码，易于维护和扩展

## 安装和使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本使用

#### 使用默认配置
```bash
python main.py
```

#### 指定策略配置
```bash
# 保守策略
python main.py --stock-universe conservative --factor-strategy conservative --time-period long_term

# 激进策略
python main.py --stock-universe aggressive --factor-strategy momentum_focused --time-period short_term

# 资金流向策略
python main.py --factor-strategy capital_flow_focused --time-period medium_term
```

#### 其他参数
```bash
# 指定推荐数量
python main.py --top-n 20

# 跳过卖出分析
python main.py --no-sell-analysis

# 使用自定义配置文件
python main.py --config my_config.yaml
```

### 3. 编程接口使用

```python
from main import StockRecommendationSystem

# 创建系统实例
system = StockRecommendationSystem(
    stock_universe='conservative',
    factor_strategy='momentum_focused',
    time_period='medium_term'
)

# 运行推荐
recommendations = system.run_recommendation(top_n=10)

# 运行卖出分析
sell_decisions = system.run_sell_analysis()
```

### 4. 运行示例

```bash
# 运行多种策略示例
python run_examples.py
```

## 系统架构

本系统采用模块化设计，各模块职责清晰，便于维护和扩展：

```
stock/
├── config.yaml           # 统一配置文件
├── data_fetcher.py        # 数据获取模块
├── feature_extractor.py   # 特征提取模块
├── scoring_engine.py      # 评分引擎模块
├── result_writer.py       # 结果输出模块
├── main.py               # 主程序入口
├── requirements.txt      # 依赖包列表
└── README.md            # 项目说明
```

### 模块说明

#### 1. 数据获取模块 (data_fetcher.py)
- **功能**: 获取股票基础数据、实时行情、历史数据、资金流向、市场情绪等
- **数据源**: 主要使用akshare库
- **特点**: 支持重试机制、股票池过滤、数据验证

#### 2. 特征提取模块 (feature_extractor.py)
- **功能**: 计算技术指标、动量因子、成交量因子、资金流向因子、情绪因子等
- **技术指标**: RSI、MACD、EMA、布林带位置、波动率等
- **特点**: 批量处理、异常处理、可配置因子权重

#### 3. 评分引擎模块 (scoring_engine.py)
- **功能**: 综合评分、股票排序、推荐理由生成
- **评分维度**: 动量、成交量、资金流向、市场情绪、风险控制
- **特点**: 多维度评分、可配置权重、智能推荐理由

#### 4. 结果输出模块 (result_writer.py)
- **功能**: 结果保存、格式化输出、Excel导出、历史数据管理
- **输出格式**: JSON、YAML、Excel
- **特点**: 自动备份、性能统计、文件管理

#### 5. 主程序 (main.py)
- **功能**: 整合各模块、命令行接口、流程控制
- **运行模式**: 推荐模式、卖出分析模式、综合模式
- **特点**: 灵活配置、错误处理、结果展示

## 安装和配置

### 1. 环境要求
- Python 3.8+
- 建议使用虚拟环境

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置文件
编辑 `config.yaml` 文件，根据需要调整参数：

```yaml
# 数据源配置
data_source:
  provider: "akshare"  # 数据提供商
  max_retries: 3       # 最大重试次数
  delay: 1             # 重试延迟(秒)

# 股票池配置
stock_universe:
  max_stocks: 500      # 最大分析股票数
  exclude_st: true     # 排除ST股票
  exclude_boards: ["688", "300"]  # 排除板块
  min_price: 3.0       # 最低价格
  max_price: 200.0     # 最高价格

# 因子权重配置
factor_weights:
  momentum_5d: 0.15
  momentum_10d: 0.20
  momentum_20d: 0.25
  rsi: 0.10
  volume_ratio: 0.15
  main_inflow_score: 0.15
  # ... 更多因子权重

# 推荐参数
recommendation:
  top_n: 20           # 推荐股票数量
  min_score: 0        # 最低推荐分数
  max_change_pct: 10  # 最大涨跌幅限制

# 输出配置
output:
  result_dir: "results"     # 结果目录
  format: "json"           # 输出格式
  backup_days: 30          # 备份天数
  enable_excel: false      # 是否启用Excel导出
```

## 使用方法

### 1. 基本用法

#### 生成买入推荐
```bash
python main.py --mode recommend
```

#### 生成卖出建议
```bash
python main.py --mode sell
```

#### 完整分析（推荐+卖出）
```bash
python main.py --mode both
```

### 2. 高级用法

#### 自定义推荐数量
```bash
python main.py --mode recommend --top-n 30
```

#### 导出Excel文件
```bash
python main.py --mode recommend --excel
```

#### 使用自定义配置文件
```bash
python main.py --config my_config.yaml
```

#### 分析指定持仓文件
```bash
python main.py --mode sell --portfolio my_portfolio.json
```

#### 静默模式（不显示结果）
```bash
python main.py --mode recommend --quiet
```

#### 不保存结果文件
```bash
python main.py --mode recommend --no-save
```

### 3. 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --config | -c | 配置文件路径 | config.yaml |
| --mode | -m | 运行模式 (recommend/sell/both) | recommend |
| --top-n | -n | 推荐股票数量 | 20 |
| --no-save | - | 不保存结果到文件 | False |
| --excel | - | 导出Excel文件 | False |
| --portfolio | -p | 持仓文件路径 | None |
| --quiet | -q | 静默模式 | False |

## 输出结果

### 1. 买入推荐结果
```json
{
  "date": "2024-01-15",
  "time": "14:45:00",
  "recommendations": [
    {
      "rank": 1,
      "stock_code": "000001",
      "stock_name": "平安银行",
      "current_price": 15.68,
      "change_pct": 2.1,
      "total_score": 8.5,
      "recommendation_reason": "动量强劲; 成交量活跃; 资金流向积极",
      "score_breakdown": {
        "momentum": 3.2,
        "volume": 2.1,
        "capital_flow": 2.0,
        "sentiment": 1.2,
        "risk": 0.0
      }
    }
  ]
}
```

### 2. 卖出决策结果
```json
{
  "date": "2024-01-15",
  "time": "09:30:00",
  "decisions": [
    {
      "stock_code": "000001",
      "stock_name": "平安银行",
      "original_price": 15.00,
      "current_price": 16.50,
      "return_rate": 10.0,
      "current_score": 6.2,
      "sell_signal": false,
      "sell_reason": "持有",
      "analysis_date": "2024-01-15 09:30:00"
    }
  ]
}
```

## 扩展和定制

### 1. 添加新的数据源
在 `data_fetcher.py` 中添加新的数据获取方法：

```python
def get_custom_data(self, stock_codes):
    """获取自定义数据源"""
    # 实现自定义数据获取逻辑
    pass
```

### 2. 添加新的技术指标
在 `feature_extractor.py` 中添加新的因子计算方法：

```python
def calculate_custom_factor(self, data):
    """计算自定义因子"""
    # 实现自定义因子计算逻辑
    pass
```

### 3. 自定义评分逻辑
在 `scoring_engine.py` 中修改评分算法：

```python
def calculate_custom_score(self, features):
    """自定义评分算法"""
    # 实现自定义评分逻辑
    pass
```

### 4. 自定义输出格式
在 `result_writer.py` 中添加新的输出格式：

```python
def export_to_custom_format(self, data):
    """导出到自定义格式"""
    # 实现自定义输出格式
    pass
```

## 性能优化

### 1. 数据缓存
- 系统支持数据缓存，避免重复获取相同数据
- 可在配置文件中设置缓存策略

### 2. 并行处理
- 特征提取支持批量处理
- 可根据系统资源调整并行度

### 3. 内存管理
- 大数据集分批处理
- 及时释放不需要的数据

## 注意事项

### 1. 数据质量
- 系统依赖外部数据源，数据质量可能影响结果
- 建议定期检查数据完整性

### 2. 市场风险
- 本系统仅供参考，不构成投资建议
- 投资有风险，决策需谨慎

### 3. 系统维护
- 定期更新依赖包
- 监控系统运行状态
- 备份重要配置和结果

## 故障排除

### 1. 常见问题

#### 数据获取失败
```
错误: 获取股票数据失败
解决: 检查网络连接，确认数据源可用
```

#### 配置文件错误
```
错误: 配置文件格式错误
解决: 检查YAML语法，确认配置项正确
```

#### 依赖包缺失
```
错误: ModuleNotFoundError
解决: 运行 pip install -r requirements.txt
```

### 2. 日志查看
系统运行日志保存在 `stock_recommendation.log` 文件中，可查看详细错误信息。

### 3. 调试模式
设置环境变量启用调试模式：
```bash
export DEBUG=1
python main.py
```

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 实现基础推荐功能
- 支持多因子评分
- 提供命令行接口

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进本项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者