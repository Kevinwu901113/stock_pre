# API接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本**: v1
- **数据格式**: JSON
- **认证方式**: JWT Token (预留)

## 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "error message",
  "detail": "detailed error information"
}
```

## 推荐接口

### 获取买入推荐

**接口地址**: `GET /api/v1/recommendations/buy`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | int | 否 | 10 | 返回数量限制(1-50) |
| min_confidence | float | 否 | 0.6 | 最小置信度(0-1) |
| strategy | string | 否 | null | 策略筛选 |

**响应示例**:
```json
[
  {
    "id": "uuid",
    "stock": {
      "code": "000001",
      "name": "平安银行",
      "current_price": 12.50
    },
    "signal": "buy",
    "confidence": 0.85,
    "target_price": 14.00,
    "stop_loss": 11.50,
    "expected_return": 0.12,
    "holding_period": 30,
    "reason": "技术指标显示突破关键阻力位",
    "strategy_name": "MA均线策略",
    "created_at": "2024-01-01T09:30:00Z"
  }
]
```

### 获取卖出推荐

**接口地址**: `GET /api/v1/recommendations/sell`

**请求参数**: 同买入推荐

**响应示例**: 同买入推荐，signal为"sell"

### 生成推荐

**接口地址**: `POST /api/v1/recommendations/generate`

**请求体**:
```json
{
  "stock_codes": ["000001", "600036"],
  "strategies": ["ma_strategy", "rsi_strategy"],
  "parameters": {
    "min_confidence": 0.7
  }
}
```

**响应示例**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "message": "推荐生成任务已提交"
}
```

### 获取推荐历史

**接口地址**: `GET /api/v1/recommendations/history`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| start_date | string | 否 | 7天前 | 开始日期(YYYY-MM-DD) |
| end_date | string | 否 | 今天 | 结束日期(YYYY-MM-DD) |
| stock_code | string | 否 | null | 股票代码筛选 |
| signal | string | 否 | null | 信号类型筛选 |
| page | int | 否 | 1 | 页码 |
| size | int | 否 | 20 | 每页数量 |

## 股票接口

### 获取股票列表

**接口地址**: `GET /api/v1/stocks`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| market | string | 否 | A | 市场类型(A/HK/US) |
| industry | string | 否 | null | 行业筛选 |
| keyword | string | 否 | null | 关键词搜索 |
| page | int | 否 | 1 | 页码 |
| size | int | 否 | 20 | 每页数量 |

**响应示例**:
```json
{
  "total": 4000,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "uuid",
      "code": "000001",
      "name": "平安银行",
      "market": "A",
      "industry": "银行",
      "sector": "金融",
      "current_price": 12.50,
      "change_pct": 0.024,
      "volume": 1000000,
      "market_cap": 240000000000
    }
  ]
}
```

### 获取股票详情

**接口地址**: `GET /api/v1/stocks/{code}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| code | string | 是 | 股票代码 |

**响应示例**:
```json
{
  "id": "uuid",
  "code": "000001",
  "name": "平安银行",
  "market": "A",
  "industry": "银行",
  "sector": "金融",
  "list_date": "1991-04-03",
  "current_price": 12.50,
  "change_pct": 0.024,
  "volume": 1000000,
  "turnover_rate": 0.15,
  "market_cap": 240000000000,
  "pe_ratio": 5.2,
  "pb_ratio": 0.8,
  "fundamentals": {
    "revenue": 150000000000,
    "net_profit": 35000000000,
    "roe": 0.12,
    "debt_ratio": 0.85
  }
}
```

### 获取股票价格数据

**接口地址**: `GET /api/v1/stocks/{code}/prices`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| start_date | string | 否 | 30天前 | 开始日期 |
| end_date | string | 否 | 今天 | 结束日期 |
| frequency | string | 否 | daily | 频率(daily/weekly/monthly) |

**响应示例**:
```json
[
  {
    "date": "2024-01-01",
    "open": 12.30,
    "high": 12.80,
    "low": 12.20,
    "close": 12.50,
    "volume": 1000000,
    "amount": 12500000,
    "turnover_rate": 0.15
  }
]
```

### 获取股票技术指标

**接口地址**: `GET /api/v1/stocks/{code}/indicators`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| indicators | string | 否 | all | 指标类型(ma,rsi,macd,kdj) |
| period | int | 否 | 30 | 计算周期 |

**响应示例**:
```json
{
  "ma": {
    "ma5": 12.45,
    "ma10": 12.30,
    "ma20": 12.10
  },
  "rsi": {
    "rsi14": 65.5
  },
  "macd": {
    "dif": 0.15,
    "dea": 0.12,
    "macd": 0.06
  }
}
```

## 策略接口

### 获取策略列表

**接口地址**: `GET /api/v1/strategies`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| category | string | 否 | null | 策略分类 |
| is_active | boolean | 否 | true | 是否激活 |

**响应示例**:
```json
[
  {
    "id": "uuid",
    "name": "MA均线策略",
    "description": "基于移动平均线的技术分析策略",
    "category": "technical",
    "parameters": {
      "short_period": 5,
      "long_period": 20
    },
    "is_active": true,
    "performance": {
      "total_return": 0.15,
      "win_rate": 0.65,
      "max_drawdown": 0.08
    }
  }
]
```

### 执行策略

**接口地址**: `POST /api/v1/strategies/{id}/execute`

**请求体**:
```json
{
  "stock_codes": ["000001", "600036"],
  "parameters": {
    "short_period": 5,
    "long_period": 20
  }
}
```

**响应示例**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "message": "策略执行任务已提交"
}
```

### 策略回测

**接口地址**: `POST /api/v1/strategies/{id}/backtest`

**请求体**:
```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 1000000,
  "stock_pool": ["000001", "600036"],
  "parameters": {
    "short_period": 5,
    "long_period": 20
  }
}
```

**响应示例**:
```json
{
  "id": "uuid",
  "total_return": 0.15,
  "annual_return": 0.15,
  "max_drawdown": 0.08,
  "sharpe_ratio": 1.2,
  "win_rate": 0.65,
  "total_trades": 120,
  "profit_trades": 78,
  "loss_trades": 42,
  "avg_profit": 0.025,
  "avg_loss": -0.015,
  "equity_curve": [
    {
      "date": "2023-01-01",
      "equity": 1000000,
      "return": 0
    }
  ],
  "trades": [
    {
      "stock_code": "000001",
      "entry_date": "2023-01-15",
      "exit_date": "2023-02-15",
      "entry_price": 12.00,
      "exit_price": 12.30,
      "quantity": 1000,
      "return": 0.025,
      "profit": 300
    }
  ]
}
```

## 数据接口

### 获取市场数据

**接口地址**: `GET /api/v1/data/market`

**请求参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| index | string | 否 | all | 指数代码 |
| date | string | 否 | 今天 | 日期 |

**响应示例**:
```json
[
  {
    "index_code": "000001",
    "index_name": "上证指数",
    "date": "2024-01-01",
    "open": 3000.0,
    "high": 3050.0,
    "low": 2980.0,
    "close": 3020.0,
    "volume": 200000000,
    "amount": 250000000000,
    "change_pct": 0.015
  }
]
```

### 同步数据

**接口地址**: `POST /api/v1/data/sync`

**请求体**:
```json
{
  "sources": ["tushare", "sina"],
  "data_types": ["prices", "fundamentals"],
  "stock_codes": ["000001", "600036"],
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**响应示例**:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "message": "数据同步任务已提交"
}
```

## 任务接口

### 获取任务状态

**接口地址**: `GET /api/v1/tasks/{task_id}`

**响应示例**:
```json
{
  "id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {},
  "error": null,
  "created_at": "2024-01-01T09:30:00Z",
  "completed_at": "2024-01-01T09:35:00Z"
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 限流说明

- 每个IP每分钟最多100次请求
- 数据同步接口每小时最多10次请求
- 策略执行接口每分钟最多5次请求

## 认证说明

目前API暂未启用认证，后续版本将支持JWT Token认证。

## 示例代码

### Python示例
```python
import requests

# 获取买入推荐
response = requests.get('http://localhost:8000/api/v1/recommendations/buy')
recommendations = response.json()

# 获取股票详情
response = requests.get('http://localhost:8000/api/v1/stocks/000001')
stock_detail = response.json()
```

### JavaScript示例
```javascript
// 获取买入推荐
fetch('http://localhost:8000/api/v1/recommendations/buy')
  .then(response => response.json())
  .then(data => console.log(data));

// 获取股票详情
fetch('http://localhost:8000/api/v1/stocks/000001')
  .then(response => response.json())
  .then(data => console.log(data));
```