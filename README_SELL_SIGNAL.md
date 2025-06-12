# 增强版卖出信号判断模块

## 概述

增强版卖出信号判断模块是一个专门用于股票交易中卖出时机判断的智能系统。该模块能够在每日9:45时对前一日推荐的股票进行精确的止盈/止损判断，包含主力资金流出检测、情绪转空判断等高级功能。

## 核心功能

### 🎯 多维度信号检测

1. **基础止盈止损**
   - 开盘涨幅超过3%触发止盈
   - 开盘跌幅超过3%触发止损
   - 快速止盈（5%以上）和紧急止损（-5%以下）

2. **主力资金流出检测**
   - 主力净流出超过5000万触发卖出
   - 连续多日主力流出预警
   - 资金流出比例异常检测

3. **市场情绪转空判断**
   - 个股情绪指数低于阈值
   - 市场整体恐慌情绪检测
   - 情绪急剧转空预警

4. **技术面风险控制**
   - 成交量异常放大检测
   - 振幅过大风险预警
   - 技术破位信号识别

### 🚨 智能操作建议

- **全部卖出**: 紧急止损、恐慌性抛售
- **减仓75%**: 快速止盈、主力大幅流出
- **减仓50%**: 标准止盈、情绪转空
- **减仓25%**: 技术面风险、轻微异常
- **继续持有**: 无明显风险信号

### 📊 结构化输出

输出JSON格式包含：
- 股票基本信息（代码、名称、价格、涨跌幅）
- 操作建议（动作、比例、紧急程度）
- 信号分析（类型、理由、置信度）
- 汇总统计（收益分布、信号分布、操作分布）

## 文件结构

```
stock/
├── enhanced_sell_signal.py      # 核心卖出信号判断模块
├── sell_signal_config.json      # 配置文件
├── test_sell_signal.py          # 测试脚本
├── daily_sell_signal_check.py   # 每日检查脚本
└── README_SELL_SIGNAL.md        # 说明文档
```

## 快速开始

### 1. 基础使用

```python
from enhanced_sell_signal import EnhancedSellSignal

# 初始化卖出信号分析器
sell_analyzer = EnhancedSellSignal('sell_signal_config.json')

# 执行分析
results = sell_analyzer.analyze_sell_signals()

# 保存结果
filename = sell_analyzer.save_results(results)
print(f"结果已保存: {filename}")
```

### 2. 运行测试

```bash
# 运行完整测试
python3 test_sell_signal.py

# 查看测试结果
ls results/sell_signals_*.json
```

### 3. 每日自动检查

```bash
# 手动执行每日检查
python3 daily_sell_signal_check.py

# 强制执行（忽略时间限制）
python3 daily_sell_signal_check.py --force

# 静默模式
python3 daily_sell_signal_check.py --quiet
```

### 4. 定时任务设置

在crontab中添加：
```bash
# 每个交易日9:45执行卖出信号检查
45 9 * * 1-5 cd /path/to/stock && python3 daily_sell_signal_check.py
```

## 配置说明

### 配置文件 (sell_signal_config.json)

```json
{
  "basic_rules": {
    "profit_threshold": 3.0,        // 止盈阈值
    "stop_loss_threshold": -3.0,    // 止损阈值
    "quick_profit_threshold": 5.0,   // 快速止盈阈值
    "emergency_stop_threshold": -5.0 // 紧急止损阈值
  },
  "fund_flow_rules": {
    "major_outflow_threshold": -50000000,  // 主力流出阈值(元)
    "outflow_ratio_threshold": 0.7,        // 流出比例阈值
    "continuous_outflow_days": 2           // 连续流出天数
  },
  "sentiment_rules": {
    "sentiment_threshold": 30,      // 情绪指数阈值
    "panic_threshold": 20,          // 恐慌阈值
    "market_fear_threshold": 0.6    // 市场恐慌比例
  },
  "technical_rules": {
    "volume_spike_ratio": 3.0,      // 成交量放大倍数
    "amplitude_threshold": 8.0,     // 振幅阈值
    "rsi_oversold": 20,             // RSI超卖
    "rsi_overbought": 80            // RSI超买
  }
}
```

### 自定义配置

可以根据不同的交易策略调整配置参数：

- **保守策略**: 降低止盈止损阈值，提高风险敏感度
- **激进策略**: 提高止盈止损阈值，降低操作频率
- **短线策略**: 缩短持有时间，提高技术面权重
- **长线策略**: 延长持有时间，降低短期波动影响

## 输出格式

### 汇总信息 (summary)

```json
{
  "total_stocks": 20,
  "action_distribution": {
    "全部卖出": 5,
    "减仓50%": 8,
    "继续持有": 7
  },
  "signal_distribution": {
    "止盈": 8,
    "止损": 5,
    "主力流出": 2
  },
  "return_stats": {
    "avg_return": 1.25,
    "positive_count": 12,
    "negative_count": 8
  }
}
```

### 详细决策 (decisions)

```json
{
  "stock_code": "600519",
  "stock_name": "贵州茅台",
  "current_price": 1680.50,
  "change_percent": 3.25,
  "action": "减仓50%",
  "sell_ratio": 0.5,
  "signal_type": "止盈",
  "reason": "达到止盈条件，开盘涨幅3.25%",
  "urgency": "MEDIUM",
  "confidence": 0.8
}
```

## 信号类型说明

### 🟢 止盈信号 (PROFIT_TAKING)
- **触发条件**: 开盘涨幅达到设定阈值
- **操作建议**: 减仓25%-75%
- **风险等级**: 低-中等

### 🔴 止损信号 (STOP_LOSS)
- **触发条件**: 开盘跌幅达到设定阈值
- **操作建议**: 减仓50%-全部卖出
- **风险等级**: 中等-高

### 💰 资金流出 (FUND_OUTFLOW)
- **触发条件**: 主力资金大幅流出
- **操作建议**: 减仓25%-75%
- **风险等级**: 中等

### 😰 情绪转空 (SENTIMENT_TURN)
- **触发条件**: 市场情绪显著恶化
- **操作建议**: 减仓25%-全部卖出
- **风险等级**: 中等-高

### 📉 技术破位 (TECHNICAL_BREAK)
- **触发条件**: 技术指标异常
- **操作建议**: 减仓25%-50%
- **风险等级**: 低-中等

## 使用场景

### 1. 日内交易
- 9:45准时检查开盘信号
- 快速响应止盈止损
- 实时监控资金流向

### 2. 短线交易
- 每日检查持仓风险
- 及时调整仓位配置
- 控制单笔损失

### 3. 中长线交易
- 定期评估持仓质量
- 识别趋势转折点
- 优化持仓结构

### 4. 风险管理
- 系统性风险预警
- 个股风险识别
- 仓位动态调整

## 注意事项

### ⚠️ 重要提醒

1. **数据依赖**: 需要可靠的实时行情数据源
2. **网络延迟**: 考虑数据获取的时间延迟
3. **交易成本**: 频繁操作会增加交易成本
4. **市场异常**: 极端市场条件下信号可能失效

### 🔧 技术要求

- Python 3.7+
- pandas, numpy
- 实时行情数据接口
- 稳定的网络连接

### 📈 性能优化

- 使用数据缓存减少API调用
- 并行处理多只股票分析
- 定期清理历史数据文件

## 扩展功能

### 🔮 未来计划

1. **机器学习增强**
   - 基于历史数据训练预测模型
   - 动态调整信号阈值
   - 个性化风险偏好设置

2. **多市场支持**
   - 支持港股、美股市场
   - 不同市场的交易时间适配
   - 汇率风险考虑

3. **高级功能**
   - 期权对冲策略
   - 组合风险管理
   - 实时推送通知

### 🔌 集成接口

```python
# 自定义数据源
class CustomDataFetcher:
    def get_stock_realtime_data(self, codes):
        # 实现自定义数据获取逻辑
        pass

# 替换数据获取器
sell_analyzer.data_fetcher = CustomDataFetcher()
```

## 常见问题

### Q: 如何调整止盈止损阈值？
A: 修改配置文件中的 `profit_threshold` 和 `stop_loss_threshold` 参数。

### Q: 可以添加自定义信号吗？
A: 可以继承 `EnhancedSellSignal` 类并重写相关方法。

### Q: 如何处理数据获取失败？
A: 系统会自动重试，失败的股票会标记为风险控制卖出。

### Q: 支持回测功能吗？
A: 当前版本主要用于实时分析，回测功能在开发计划中。

## 技术支持

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: support@example.com
- 📱 微信: trading_support
- 🐛 Issues: GitHub Issues

---

**免责声明**: 本模块仅供参考，不构成投资建议。投资有风险，决策需谨慎。