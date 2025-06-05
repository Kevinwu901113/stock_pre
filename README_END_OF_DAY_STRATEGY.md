# 尾盘买入、早盘卖出策略功能说明

## 功能概述

本系统实现了完整的"尾盘买入、早盘卖出"核心功能，包括策略执行、推荐生成、定时任务调度等模块。

## 核心组件

### 1. 策略模块

#### 尾盘买入策略 (`EndOfDayStrategy`)
- **文件位置**: `/strategies/end_of_day.py`
- **执行时间**: 每个交易日 14:55
- **主要逻辑**:
  - 分析连续上涨天数
  - 检查成交量放大情况
  - 技术指标突破分析
  - 尾盘拉升信号识别

#### 早盘卖出策略 (`MorningExitStrategy`)
- **文件位置**: `/strategies/end_of_day.py`
- **执行时间**: 每个交易日 09:35
- **主要逻辑**:
  - 目标收益达成检查
  - 止损触发分析
  - 技术指标转弱判断
  - 开盘跳空分析

### 2. API接口

#### 推荐生成接口
- **路径**: `POST /api/recommendations/generate`
- **功能**: 根据指定策略生成推荐
- **参数**:
  ```json
  {
    "strategy_type": "end_of_day",
    "parameters": {
      "consecutive_days": 2,
      "volume_multiplier": 1.5,
      "min_confidence": 0.6
    }
  }
  ```

#### 定时任务接口
- **路径**: `POST /api/recommendations/scheduled-task`
- **功能**: 执行定时任务（尾盘买入或早盘卖出）
- **参数**:
  ```json
  {
    "task_type": "end_of_day"
  }
  ```

#### 获取推荐接口（已更新）
- **买入推荐**: `GET /api/recommendations/buy?date=2024-01-15`
- **卖出推荐**: `GET /api/recommendations/sell?date=2024-01-15`
- **新增功能**: 支持按日期筛选推荐

### 3. 定时任务调度

#### 调度器配置
- **文件位置**: `/backend/app/core/scheduler.py`
- **调度框架**: APScheduler
- **时区**: Asia/Shanghai

#### 定时任务列表
1. **尾盘买入策略**: 每个交易日 14:55 执行
2. **早盘卖出策略**: 每个交易日 09:35 执行
3. **推荐清理任务**: 每天 21:00 清理过期推荐
4. **市场数据同步**: 每个交易日 15:30 同步数据

### 4. 数据库模型更新

#### Recommendation 表新增字段
- `signal_type`: 信号类型（如 'end_of_day', 'morning_exit'）
- `expected_return`: 预期收益率
- `holding_period`: 持有周期（天数）
- `risk_level`: 风险等级（'low', 'medium', 'high'）

#### 新增索引
- `idx_recommendation_signal_created`: 基于 signal_type 和 created_at 的复合索引

## 使用方法

### 1. 启动应用

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 2. 手动执行策略

```bash
# 执行尾盘买入策略
curl -X POST "http://localhost:8000/api/recommendations/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "end_of_day",
    "parameters": {
      "consecutive_days": 2,
      "volume_multiplier": 1.5,
      "min_confidence": 0.6
    }
  }'

# 执行早盘卖出策略
curl -X POST "http://localhost:8000/api/recommendations/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "morning_exit",
    "parameters": {
      "target_return": 0.05,
      "stop_loss_ratio": 0.03,
      "min_confidence": 0.6
    }
  }'
```

### 3. 查看推荐结果

```bash
# 获取今日买入推荐
curl "http://localhost:8000/api/recommendations/buy"

# 获取指定日期的买入推荐
curl "http://localhost:8000/api/recommendations/buy?date=2024-01-15"

# 获取今日卖出推荐
curl "http://localhost:8000/api/recommendations/sell"

# 获取指定日期的卖出推荐
curl "http://localhost:8000/api/recommendations/sell?date=2024-01-15"
```

### 4. 查看活跃推荐

```bash
# 获取当前活跃的推荐
curl "http://localhost:8000/api/recommendations/active"
```

## 配置说明

### 策略参数配置

#### 尾盘买入策略参数
- `consecutive_days`: 连续上涨天数阈值（默认: 2）
- `volume_multiplier`: 成交量放大倍数（默认: 1.5）
- `daily_gain_threshold`: 单日涨幅阈值（默认: 0.03）
- `rsi_threshold`: RSI阈值（默认: 70）
- `ma_period`: 移动平均线周期（默认: 20）
- `min_confidence`: 最小置信度（默认: 0.6）

#### 早盘卖出策略参数
- `target_return`: 目标收益率（默认: 0.05）
- `stop_loss_ratio`: 止损比例（默认: 0.03）
- `gap_threshold`: 跳空阈值（默认: 0.02）
- `rsi_sell_threshold`: RSI卖出阈值（默认: 30）
- `min_confidence`: 最小置信度（默认: 0.6）

### 调度器配置

调度器会在应用启动时自动启动，在应用关闭时自动停止。可以通过以下方式查看调度器状态：

```python
from app.core.scheduler import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_all_jobs()
print(jobs)
```

## 注意事项

1. **交易日判断**: 当前实现仅检查周一到周五，实际应用中需要考虑节假日
2. **数据依赖**: 策略执行需要股票价格、成交量等基础数据
3. **风险控制**: 建议设置合理的置信度阈值和风险控制参数
4. **监控告警**: 生产环境建议添加任务执行状态监控和异常告警
5. **数据备份**: 重要的推荐数据建议定期备份

## 扩展功能

### 1. 添加新策略

在 `/strategies/` 目录下创建新的策略文件，继承 `BaseStrategy` 类：

```python
from strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def execute(self, stock_codes, **kwargs):
        # 实现策略逻辑
        pass
    
    def get_description(self):
        return "自定义策略描述"
    
    def get_parameters_schema(self):
        return {
            "param1": {"type": "number", "default": 1.0}
        }
```

### 2. 自定义调度时间

修改 `scheduler.py` 中的 `_setup_jobs` 方法，添加新的定时任务：

```python
self.scheduler.add_job(
    func=self._custom_task,
    trigger=CronTrigger(hour=10, minute=30),
    id='custom_task',
    name='自定义任务'
)
```

### 3. 添加通知功能

可以在策略执行完成后添加邮件、短信或微信通知功能，及时告知用户推荐结果。

## 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLAlchemy + PostgreSQL/MySQL
- **任务调度**: APScheduler
- **缓存**: Redis
- **日志**: Loguru
- **数据分析**: Pandas, NumPy
- **技术分析**: TA-Lib

## 联系方式

如有问题或建议，请联系开发团队。