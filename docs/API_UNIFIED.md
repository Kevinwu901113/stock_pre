# 统一API接口规范文档

## 概述

本文档描述了股票推荐系统后端API的统一规范，包括RESTful风格的接口设计、统一响应格式和字段命名规范。

## 1. RESTful接口设计

### 1.1 路径命名规范

所有接口路径遵循RESTful风格：

- **股票相关**：
  - `GET /stocks` - 获取股票列表
  - `GET /stocks/{code}` - 获取股票详情
  - `GET /stocks/search` - 搜索股票
  - `GET /stocks/suggest` - 股票搜索建议
  - `GET /stocks/{code}/kline` - 获取K线数据
  - `GET /stocks/{code}/realtime` - 获取实时数据
  - `GET /stocks/{code}/indicators` - 获取技术指标
  - `GET /stocks/{code}/indicators/ma` - 获取MA指标
  - `GET /stocks/{code}/indicators/macd` - 获取MACD指标

- **推荐相关**：
  - `GET /recommendations` - 获取推荐列表
  - `GET /recommendations/buy` - 获取买入推荐
  - `GET /recommendations/sell` - 获取卖出推荐
  - `POST /recommendations` - 创建推荐
  - `PUT /recommendations/{id}` - 更新推荐
  - `DELETE /recommendations/{id}` - 删除推荐

### 1.2 HTTP方法使用

- `GET` - 获取资源
- `POST` - 创建资源
- `PUT` - 更新资源（完整更新）
- `PATCH` - 更新资源（部分更新）
- `DELETE` - 删除资源

## 2. 统一响应格式

### 2.1 成功响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体数据内容
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "requestId": "req_123456789"
}
```

### 2.2 错误响应格式

```json
{
  "code": 400,
  "message": "参数错误",
  "data": {
    "details": "具体错误信息"
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "requestId": "req_123456789"
}
```

### 2.3 分页响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      // 数据列表
    ],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5,
    "hasNext": true,
    "hasPrev": false
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## 3. 字段命名规范

### 3.1 API响应字段

- 统一使用 **camelCase** 命名风格
- 数据库字段使用 **snake_case**，在API响应时自动转换为 **camelCase**

### 3.2 字段转换示例

数据库字段 → API响应字段：
- `stock_code` → `stockCode`
- `trade_date` → `tradeDate`
- `open_price` → `openPrice`
- `close_price` → `closePrice`
- `market_cap` → `marketCap`
- `pe_ratio` → `peRatio`
- `pb_ratio` → `pbRatio`
- `turnover_rate` → `turnoverRate`
- `confidence_score` → `confidenceScore`
- `target_price` → `targetPrice`
- `stop_loss_price` → `stopLossPrice`
- `expected_return` → `expectedReturn`
- `holding_period` → `holdingPeriod`
- `risk_level` → `riskLevel`
- `created_at` → `createdAt`
- `updated_at` → `updatedAt`

## 4. 新增接口说明

### 4.1 股票搜索接口

#### 搜索股票
```
GET /stocks/search?q={keyword}&market={market}&industry={industry}&page={page}&size={size}
```

参数：
- `q`: 搜索关键词（必填）
- `market`: 市场筛选（可选）
- `industry`: 行业筛选（可选）
- `page`: 页码（默认1）
- `size`: 每页数量（默认20）

#### 搜索建议
```
GET /stocks/suggest?q={keyword}&limit={limit}
```

参数：
- `q`: 搜索关键词（必填）
- `limit`: 建议数量（默认10）

### 4.2 K线数据接口

#### 获取K线数据
```
GET /stocks/{code}/kline?period={period}&start_date={start}&end_date={end}&limit={limit}
```

参数：
- `period`: K线周期（1d/1w/1m，默认1d）
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）
- `limit`: 数量限制（默认100）

#### 获取实时数据
```
GET /stocks/{code}/realtime
```

### 4.3 技术指标接口

#### 获取综合技术指标
```
GET /stocks/{code}/indicators?indicators={list}&period={period}
```

参数：
- `indicators`: 指标列表（ma,macd,rsi,kdj,boll,cci,williams）
- `period`: 计算周期（默认20）

#### 获取MA指标
```
GET /stocks/{code}/indicators/ma?periods={periods}
```

参数：
- `periods`: MA周期列表（如：5,10,20,60）

#### 获取MACD指标
```
GET /stocks/{code}/indicators/macd?fast_period={fast}&slow_period={slow}&signal_period={signal}
```

参数：
- `fast_period`: 快线周期（默认12）
- `slow_period`: 慢线周期（默认26）
- `signal_period`: 信号线周期（默认9）

## 5. 状态码说明

- `200` - 成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 禁止访问
- `404` - 资源不存在
- `422` - 请求参数验证失败
- `500` - 服务器内部错误
- `503` - 服务不可用

## 6. 错误处理

### 6.1 参数验证错误

```json
{
  "code": 400,
  "message": "参数验证失败",
  "data": {
    "field": "stock_code",
    "details": "股票代码格式不正确"
  }
}
```

### 6.2 资源不存在错误

```json
{
  "code": 404,
  "message": "股票不存在",
  "data": {
    "stockCode": "000001"
  }
}
```

### 6.3 服务器错误

```json
{
  "code": 500,
  "message": "服务器内部错误",
  "data": {
    "details": "数据库连接失败"
  }
}
```

## 7. 版本控制

- API版本通过URL路径控制：`/api/v1/stocks`
- 当前版本：v1
- 向后兼容性：保持至少两个版本的兼容性

## 8. 性能优化

### 8.1 缓存策略

- 股票基础信息：缓存1小时
- 实时价格数据：缓存1分钟
- 技术指标数据：缓存5分钟
- 推荐数据：缓存10分钟

### 8.2 分页限制

- 默认页面大小：20
- 最大页面大小：100
- 建议使用游标分页处理大数据集

## 9. 安全考虑

### 9.1 请求限制

- 每个IP每分钟最多100个请求
- 每个用户每分钟最多200个请求

### 9.2 数据验证

- 所有输入参数进行严格验证
- SQL注入防护
- XSS攻击防护

## 10. 监控和日志

### 10.1 请求日志

- 记录所有API请求和响应
- 包含请求ID用于追踪
- 记录响应时间和状态码

### 10.2 错误监控

- 实时监控错误率
- 异常情况自动告警
- 性能指标监控