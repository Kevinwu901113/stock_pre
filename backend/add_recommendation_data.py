#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/wjk/workplace/stock')
sys.path.append('/home/wjk/workplace/stock/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from app.models.stock import Stock, Recommendation

def add_test_data():
    """添加测试数据"""
    try:
        # 创建数据库连接
        DATABASE_URL = "sqlite:///./stock_data.db"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 添加测试股票数据
        stocks_data = [
            {"code": "000001", "name": "平安银行", "market": "SZ", "industry": "银行", "sector": "金融业"},
            {"code": "000002", "name": "万科A", "market": "SZ", "industry": "房地产", "sector": "房地产业"},
            {"code": "600000", "name": "浦发银行", "market": "SH", "industry": "银行", "sector": "金融业"},
        ]
        
        for stock_data in stocks_data:
            existing_stock = db.query(Stock).filter(Stock.code == stock_data["code"]).first()
            if not existing_stock:
                stock = Stock(**stock_data)
                db.add(stock)
        
        # 添加测试推荐数据
        recommendations_data = [
            {
                "stock_code": "000001",
                "recommendation_type": "buy",
                "strategy_name": "技术分析策略",
                "confidence_score": 0.85,
                "target_price": 15.50,
                "stop_loss_price": 13.20,
                "reason": "技术指标显示上涨趋势",
                "signal_type": "technical_breakthrough",
                "expected_return": 0.12,
                "holding_period": "1-3天",
                "risk_level": "medium",
                "created_at": datetime.now(),
                "is_active": True
            },
            {
                "stock_code": "000002",
                "recommendation_type": "buy",
                "strategy_name": "基本面分析策略",
                "confidence_score": 0.78,
                "target_price": 25.80,
                "stop_loss_price": 22.50,
                "reason": "基本面良好，估值合理",
                "signal_type": "fundamental_value",
                "expected_return": 0.08,
                "holding_period": "1周",
                "risk_level": "low",
                "created_at": datetime.now(),
                "is_active": True
            },
            {
                "stock_code": "600000",
                "recommendation_type": "sell",
                "strategy_name": "风险控制策略",
                "confidence_score": 0.72,
                "target_price": 11.20,
                "stop_loss_price": 12.80,
                "reason": "技术指标显示下跌风险",
                "signal_type": "risk_control",
                "expected_return": -0.05,
                "holding_period": "1-3天",
                "risk_level": "high",
                "created_at": datetime.now(),
                "is_active": True
            }
        ]
        
        for rec_data in recommendations_data:
            recommendation = Recommendation(**rec_data)
            db.add(recommendation)
        
        db.commit()
        print("测试数据添加成功")
        
        # 验证数据
        stock_count = db.query(Stock).count()
        rec_count = db.query(Recommendation).count()
        print(f"股票数据: {stock_count} 条")
        print(f"推荐数据: {rec_count} 条")
        
        db.close()
        
    except Exception as e:
        print(f"添加测试数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_data()