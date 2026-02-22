from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import SessionLocal
from db.models import LFA1, RBKP, AiVendor, AiInvoice
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
    API endpoint to PULL data from SAP and PUSH to AI schema.
    This integrates the logic previously demoed in the sync service.
    """
    stats = {"vendors_synced": 0, "invoices_synced": 0}
    
    # 1. Sync Vendors
    sap_vendors = db.query(LFA1).limit(limit).all()
    for v in sap_vendors:
        ai_v = db.query(AiVendor).filter(AiVendor.LIFNR == v.LIFNR).first()
        if not ai_v:
            ai_v = AiVendor(
                LIFNR=v.LIFNR,
                NAME1=v.NAME1,
                AI_Score=80, # Placeholder logic
                AI_Classification="Synced via API",
                last_synced_at=datetime.utcnow()
            )
            db.add(ai_v)
            stats["vendors_synced"] += 1
        else:
            ai_v.NAME1 = v.NAME1
            ai_v.last_synced_at = datetime.utcnow()

    # 2. Sync Invoices
    sap_invoices = db.query(RBKP).limit(limit).all()
    for inv in sap_invoices:
        ai_inv = db.query(AiInvoice).filter(
            AiInvoice.BELNR == inv.BELNR, 
            AiInvoice.GJAHR == inv.GJAHR
        ).first()
        
        if not ai_inv:
            is_anomalous = 1 if (inv.RMWWR or 0) > 150000 else 0
            ai_inv = AiInvoice(
                BELNR=inv.BELNR,
                GJAHR=inv.GJAHR,
                LIFNR=inv.LIFNR,
                TotalAmount=int(inv.RMWWR or 0),
                Anomalous=is_anomalous,
                last_synced_at=datetime.utcnow()
            )
            db.add(ai_inv)
            stats["invoices_synced"] += 1

    db.commit()
    return {"status": "success", "synced_records": stats}

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
