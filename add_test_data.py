#!/usr/bin/env python3
import os
import sys

# 设置环境变量和路径
os.environ['DATABASE_URL'] = 'sqlite:////home/wjk/workplace/stock/data/stock.db'
sys.path.append('/home/wjk/workplace/stock/backend')

from app.models.stock import Stock
from config.database import get_db
from sqlalchemy.orm import Session

def add_test_data():
    db = next(get_db())
    try:
        # 添加测试股票
        stocks = [
            Stock(code='000001', name='平安银行', market='SZ', industry='银行', sector='金融业', is_active=True),
            Stock(code='000002', name='万科A', market='SZ', industry='房地产', sector='房地产业', is_active=True),
            Stock(code='600000', name='浦发银行', market='SH', industry='银行', sector='金融业', is_active=True),
        ]
        
        for stock in stocks:
            db.add(stock)
        
        db.commit()
        print(f'成功添加 {len(stocks)} 只测试股票')
        
    except Exception as e:
        db.rollback()
        print(f'添加测试数据失败: {e}')
    finally:
        db.close()

if __name__ == '__main__':
    add_test_data()