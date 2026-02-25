# MASTER APPLICATION FILE: API, Logic, and Setup
import os
import sys
import random
from datetime import date, datetime
from typing import List
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, joinedload

# 1. Load Environment & Models
load_dotenv()
from models import Base, LFA1, EKKO, EKPO, RBKP, AiVendor, AiInvoice

# 2. Database Connection Setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Simplified TAI App")

# --- UTILITY: Get Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- LOGIC: Sync SAP to AI ---
def sync_data_logic(db: Session):
    """Business Logic to process SAP data into AI insights."""
    sap_vendors = db.query(LFA1).all()
    stats = {"synced": 0}
    for v in sap_vendors:
        ai_v = db.query(AiVendor).filter(AiVendor.LIFNR == v.LIFNR).first()
        if not ai_v:
            db.add(AiVendor(
                LIFNR=v.LIFNR, NAME1=v.NAME1, AI_Score=random.randint(70,99),
                AI_Classification="Automated", last_synced_at=datetime.utcnow()
            ))
            stats["synced"] += 1
    db.commit()
    return stats

# --- ROUTES ---

@app.get("/")
def home():
    return {"message": "Simplified TAI Application is Online"}

@app.get("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    """Runs the sync process via simple API call."""
    return sync_data_logic(db)

@app.get("/bulk-purchase")
def bulk_purchase(db: Session = Depends(get_db)):
    """Returns Purchase Orders and Line Items in requested JSON format."""
    data = db.query(EKKO).options(joinedload(EKKO.line_items)).limit(10).all()
    return {
        "data": [{
            "P_id": p.EBELN,
            "line_items": [{"prod": l.MATNR, "qty": l.MENGE, "price": l.NETPR} for l in p.line_items],
            "MapJSn": {"purchase": {"SAP_PO_ID": p.EBELN}, "vendor": {"purchase_id": p.LIFNR}}
        } for p in data]
    }

# --- MASTER SETUP COMMAND ---
def setup_application():
    """Initializes schemas, tables, and test data in one go."""
    print("Setting up system...")
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS sap;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai;"))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # Add 1 test record if none exist
    if not db.query(LFA1).first():
        lifnr = f"V{random.randint(1000,9999)}"
        db.add(LFA1(LIFNR=lifnr, NAME1="Test Vendor", COUNTRY="IN", ERDAT=date.today()))
        db.add(EKKO(EBELN=f"45{random.randint(1000,9999)}", LIFNR=lifnr, BEDAT=date.today()))
        db.commit()
    db.close()
    print("Setup complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_application()
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
