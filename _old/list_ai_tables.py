from sqlalchemy import text
from db.base import SessionLocal

db = SessionLocal()
try:
    tables = [r[0] for r in db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'ai'")).fetchall()]
    print("Tables in AI schema:")
    for t in sorted(tables):
        print(f" - {t}")
finally:
    db.close()
