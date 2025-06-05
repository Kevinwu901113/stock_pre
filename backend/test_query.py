#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/wjk/workplace/stock')
sys.path.append('/home/wjk/workplace/stock/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
# 直接使用SQLite数据库路径
DB_URL = "sqlite:///./stock_data.db"

def test_simple_query():
    """测试简单的数据库查询"""
    try:
        # 创建数据库连接
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 测试简单查询
        print("测试1: 查询推荐表")
        result = db.execute(text("SELECT COUNT(*) FROM recommendations"))
        count = result.scalar()
        print(f"推荐记录总数: {count}")
        
        print("\n测试2: 查询股票表")
        result = db.execute(text("SELECT COUNT(*) FROM stocks"))
        count = result.scalar()
        print(f"股票记录总数: {count}")
        
        print("\n测试3: 查询活跃推荐")
        result = db.execute(text("SELECT COUNT(*) FROM recommendations WHERE is_active = 1"))
        count = result.scalar()
        print(f"活跃推荐数: {count}")
        
        print("\n测试4: 联合查询")
        query = """
        SELECT r.id, r.stock_code, s.name 
        FROM recommendations r 
        LEFT JOIN stocks s ON r.stock_code = s.code 
        WHERE r.is_active = 1 
        LIMIT 5
        """
        result = db.execute(text(query))
        rows = result.fetchall()
        print(f"联合查询结果数: {len(rows)}")
        for row in rows:
            print(f"  ID: {row[0]}, 代码: {row[1]}, 名称: {row[2]}")
            
        db.close()
        print("\n数据库查询测试完成")
        
    except Exception as e:
        print(f"查询测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_query()