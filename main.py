from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import SessionLocal
from db.models import LFA1, RBKP, AiVendor, AiInvoice
from db.services.ai_sync_service import SyncService
from datetime import datetime
from typing import List

app = FastAPI(title="TAI Data API", description="Enterprise SAP-AI Synchronization API")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to TAI Data API", "status": "online"}

@app.get("/sync/sap-to-ai")
def sync_data(limit: int = 100, db: Session = Depends(get_db)):
    """
    API endpoint to PULL data from SAP and PUSH to AI schema via SyncService.
    """
    try:
        stats = SyncService.sync_sap_to_ai(db, limit)
        return {"status": "success", "synced_records": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sap/vendors")
def get_sap_vendors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vendors = db.query(LFA1).offset(skip).limit(limit).all()
    # Simple conversion to dict for response
    return [{"LIFNR": v.LIFNR, "NAME1": v.NAME1, "COUNTRY": v.COUNTRY} for v in vendors]

@app.get("/ai/vendors")
def get_ai_vendors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vendors = db.query(AiVendor).offset(skip).limit(limit).all()
    return [{"LIFNR": v.LIFNR, "NAME1": v.NAME1, "AI_Score": v.AI_Score} for v in vendors]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
