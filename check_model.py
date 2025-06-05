#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/wjk/workplace/stock')

from config.database import SessionLocal, engine
from backend.app.models.stock import Recommendation
from sqlalchemy import inspect

def check_model():
    print('Checking Recommendation model...')
    print('Table name:', Recommendation.__tablename__)
    print('Table:', Recommendation.__table__)
    
    # Check if table exists in database
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print('\nTables in database:', tables)
    
    if 'recommendations' in tables:
        columns = inspector.get_columns('recommendations')
        print('\nColumns in recommendations table:')
        for col in columns:
            print(f'  {col["name"]}: {col["type"]}')
    
    # Check model registry
    print('\nModel registry:')
    for name, model in Recommendation.registry._class_registry.items():
        if hasattr(model, '__tablename__'):
            print(f'  {name}: {model.__tablename__}')
    
    # Test simple query compilation
    db = SessionLocal()
    try:
        from sqlalchemy.orm import Query
        query = db.query(Recommendation)
        print('\nQuery object:', query)
        print('Query statement:', query.statement)
        print('Compiled query:', query.statement.compile(compile_kwargs={"literal_binds": True}))
    except Exception as e:
        print('Query compilation error:', e)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_model()