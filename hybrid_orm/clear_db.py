from config_db import SessionLocal, SapData
from sqlalchemy import text

def clear_db():
    print("Clearing sap_data table...")
    with SessionLocal() as db:
        try:
            n = db.query(SapData).delete()
            db.commit()
            db.execute(text("ALTER SEQUENCE hybrid_orm.sap_data_id_seq RESTART WITH 1;"))
            db.commit()
            print(f"Deleted {n} rows. ID reset to 1.")
        except Exception as e:
            db.rollback()
            print(f"Error: {e}")

if __name__ == "__main__":
    clear_db()
