from sqlalchemy import text
from db.base import SessionLocal

db = SessionLocal()
try:
    results = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'ai'
    """)).fetchall()
    
    print("\n--- Rows in AI Schema Tables ---")
    for row in results:
        table = row[0]
        cnt = db.execute(text(f"SELECT count(*) FROM ai.{table}")).scalar()
        print(f"Table ai.{table}: {cnt} records")
finally:
    db.close()
