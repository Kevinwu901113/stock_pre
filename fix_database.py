#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/wjk/workplace/stock')

from config.database import SessionLocal, engine, Base
from backend.app.models.stock import *
from sqlalchemy import text
import os

def fix_database():
    print('=== Fixing Database ===')
    
    # Check if database file exists
    db_files = ['stock.db', 'stock_data.db']
    for db_file in db_files:
        if os.path.exists(f'/home/wjk/workplace/stock/backend/{db_file}'):
            print(f'Found database file: {db_file}')
    
    # Drop all tables and recreate
    print('\nDropping all tables...')
    Base.metadata.drop_all(bind=engine)
    
    print('Creating all tables...')
    Base.metadata.create_all(bind=engine)
    
    # Test the fixed database
    print('\nTesting database...')
    db = SessionLocal()
    try:
        # Test direct SQL
        result = db.execute(text('SELECT COUNT(*) FROM recommendations'))
        count = result.fetchone()[0]
        print(f'Direct SQL count: {count}')
        
        # Test ORM query
        orm_count = db.query(Recommendation).count()
        print(f'ORM count: {orm_count}')
        
        print('Database fix successful!')
        
    except Exception as e:
        print(f'Database test failed: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    fix_database()