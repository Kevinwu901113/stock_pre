#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/wjk/workplace/stock')

from config.database import SessionLocal, engine
from backend.app.models.stock import Recommendation
from sqlalchemy import text

def test_sql_issue():
    db = SessionLocal()
    
    try:
        print('Testing direct SQL...')
        result = db.execute(text('SELECT COUNT(*) FROM recommendations'))
        print('Direct SQL works:', result.fetchone())
        
        print('\nTesting ORM query...')
        query = db.query(Recommendation).limit(1)
        print('Generated SQL:', str(query))
        
        result_data = query.all()
        print('ORM query works, found:', len(result_data))
        
    except Exception as e:
        print('Error:', str(e))
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    test_sql_issue()