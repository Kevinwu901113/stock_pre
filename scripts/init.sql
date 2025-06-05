-- A股量化选股推荐系统数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS stock_db;

-- 使用数据库
\c stock_db;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 股票基础信息表
CREATE TABLE IF NOT EXISTS stocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'A', -- A股、港股、美股
    industry VARCHAR(50),
    sector VARCHAR(50),
    list_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 股票价格数据表
CREATE TABLE IF NOT EXISTS stock_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open DECIMAL(10,3) NOT NULL,
    high DECIMAL(10,3) NOT NULL,
    low DECIMAL(10,3) NOT NULL,
    close DECIMAL(10,3) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(15,2),
    turnover_rate DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- 股票基本面数据表
CREATE TABLE IF NOT EXISTS stock_fundamentals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    pe_ratio DECIMAL(10,4),
    pb_ratio DECIMAL(10,4),
    market_cap DECIMAL(15,2),
    total_share BIGINT,
    float_share BIGINT,
    revenue DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    roe DECIMAL(8,4),
    debt_ratio DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- 策略定义表
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- technical, fundamental, sentiment
    parameters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 推荐记录表
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id UUID REFERENCES stocks(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    signal VARCHAR(10) NOT NULL, -- buy, sell, hold
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    target_price DECIMAL(10,3),
    stop_loss DECIMAL(10,3),
    expected_return DECIMAL(8,4),
    holding_period INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_return DECIMAL(8,4),
    annual_return DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    win_rate DECIMAL(8,4),
    total_trades INTEGER,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表（预留）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stocks_code ON stocks(code);
CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_date ON stock_prices(stock_id, date);
CREATE INDEX IF NOT EXISTS idx_stock_fundamentals_date ON stock_fundamentals(date);
CREATE INDEX IF NOT EXISTS idx_recommendations_signal ON recommendations(signal);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at);
CREATE INDEX IF NOT EXISTS idx_recommendations_active ON recommendations(is_active);

-- 插入示例策略数据
INSERT INTO strategies (name, description, category, parameters) VALUES
('MA均线策略', '基于移动平均线的技术分析策略', 'technical', '{"short_period": 5, "long_period": 20}'),
('RSI相对强弱指标', '基于RSI指标的超买超卖策略', 'technical', '{"period": 14, "overbought": 70, "oversold": 30}'),
('PE估值策略', '基于市盈率的基本面分析策略', 'fundamental', '{"pe_threshold": 15, "industry_comparison": true}'),
('成交量突破策略', '基于成交量异动的技术策略', 'technical', '{"volume_ratio": 2.0, "price_change": 0.03}')
ON CONFLICT (name) DO NOTHING;

-- 插入示例股票数据
INSERT INTO stocks (code, name, market, industry, sector) VALUES
('000001', '平安银行', 'A', '银行', '金融'),
('000002', '万科A', 'A', '房地产开发', '房地产'),
('600000', '浦发银行', 'A', '银行', '金融'),
('600036', '招商银行', 'A', '银行', '金融'),
('600519', '贵州茅台', 'A', '白酒', '消费'),
('000858', '五粮液', 'A', '白酒', '消费'),
('002415', '海康威视', 'A', '安防设备', '科技'),
('300059', '东方财富', 'A', '证券', '金融')
ON CONFLICT (code) DO NOTHING;

COMMIT;