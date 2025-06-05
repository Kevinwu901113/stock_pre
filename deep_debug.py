#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/wjk/workplace/stock')

from config.database import SessionLocal, engine, Base
from backend.app.models.stock import Recommendation
from sqlalchemy import inspect, text
from sqlalchemy.orm import Query
from sqlalchemy.sql import visitors

def debug_query_generation():
    print('=== Deep Debug SQL Generation ===')
    
    # Check Base and metadata
    print(f'Base: {Base}')
    print(f'Base.metadata: {Base.metadata}')
    print(f'Base.metadata.tables: {list(Base.metadata.tables.keys())}')
    
    # Check Recommendation model
    print(f'\nRecommendation.__table__: {Recommendation.__table__}')
    print(f'Recommendation.__tablename__: {Recommendation.__tablename__}')
    print(f'Recommendation.__table__.name: {Recommendation.__table__.name}')
    
    # Check if table is properly registered
    if 'recommendations' in Base.metadata.tables:
        table = Base.metadata.tables['recommendations']
        print(f'\nTable from metadata: {table}')
        print(f'Table name: {table.name}')
        print(f'Table columns: {[c.name for c in table.columns]}')
    
    # Create session and test query
    db = SessionLocal()
    try:
        # Create query object
        query = db.query(Recommendation)
        print(f'\nQuery object: {query}')
        print(f'Query statement: {query.statement}')
        
        # Try to compile the query
        try:
            compiled = query.statement.compile()
            print(f'\nCompiled query: {compiled}')
            print(f'Query string: {str(compiled)}')
        except Exception as e:
            print(f'Compilation error: {e}')
            
        # Check the query's column clause
        print(f'\nQuery column clause: {query.statement.column_clause}')
        print(f'Query from clause: {query.statement.froms}')
        
        # Try a simple count query
        print('\n=== Testing Count Query ===')
        count_query = db.query(Recommendation).count()
        print(f'Count result: {count_query}')
        
    except Exception as e:
        print(f'Query error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    debug_query_generation()