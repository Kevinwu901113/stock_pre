-- SQLite版本的数据库初始化脚本

-- 股票基础信息表
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'A',
    industry VARCHAR(50),
    sector VARCHAR(50),
    list_date DATE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 股票价格数据表
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,3) NOT NULL,
    high DECIMAL(10,3) NOT NULL,
    low DECIMAL(10,3) NOT NULL,
    close DECIMAL(10,3) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(15,2),
    turnover_rate DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, date),
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 推荐表
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    recommendation_type VARCHAR(10) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    target_price DECIMAL(10,3),
    stop_loss_price DECIMAL(10,3),
    reason TEXT,
    signal_type VARCHAR(50),
    expected_return DECIMAL(8,4),
    holding_period INTEGER,
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 策略结果表
CREATE TABLE IF NOT EXISTS strategy_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    signal_strength DECIMAL(5,4) NOT NULL,
    entry_price DECIMAL(10,3),
    exit_price DECIMAL(10,3),
    return_rate DECIMAL(8,4),
    holding_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES stocks(code)
);

-- 插入测试股票数据
INSERT OR IGNORE INTO stocks (code, name, market, sector) VALUES 
('000001', '平安银行', 'A', '银行'),
('000002', '万科A', 'A', '房地产'),
('600000', '浦发银行', 'A', '银行');

-- 插入测试推荐数据
INSERT OR IGNORE INTO recommendations (stock_code, recommendation_type, strategy_name, confidence_score, target_price, reason, created_at, is_active) VALUES 
('000001', 'buy', 'test_strategy', 0.8, 15.0, '测试买入推荐', datetime('now'), 1),
('000002', 'sell', 'test_strategy', 0.7, 25.0, '测试卖出推荐', datetime('now'), 1);