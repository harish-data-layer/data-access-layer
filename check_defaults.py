from db.base import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("AI Vendors id default:")
    for row in conn.execute(text("SELECT column_name, column_default FROM information_schema.columns WHERE table_schema = 'ai' AND table_name = 'ai_vendors'")):
        print(row)
    print("Promoted Vendors vendor_id default:")
    for row in conn.execute(text("SELECT column_name, column_default FROM information_schema.columns WHERE table_schema = 'ai' AND table_name = 'promoted_vendors'")):
        print(row)
