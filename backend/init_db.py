#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/wjk/workplace/stock')
sys.path.append('/home/wjk/workplace/stock/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入所有模型
from app.models.stock import Base

def init_database():
    """初始化数据库"""
    try:
        # 创建数据库引擎
        DATABASE_URL = "sqlite:///./stock_data.db"
        engine = create_engine(DATABASE_URL, echo=True)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("数据库初始化成功")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_database()