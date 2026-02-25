# Import FastAPI to create the web application and routing
from fastapi import FastAPI, Depends, HTTPException
# Import Session for database transaction management
from sqlalchemy.orm import Session
# Import SessionLocal to initialize database connectivity for each request
from db.base import SessionLocal
# Import Models to define what data looks like in responses and queries
from db.models import LFA1, RBKP, AiVendor, AiInvoice
# Import SyncService to consolidate the 'Pull and Push' logic
from db.services.ai_sync_service import SyncService
# Import datetime for timestamping and timing
from datetime import datetime
# Import List for type hinting response variations
from typing import List

# Initialize the FastAPI application with metadata
app = FastAPI(
    title="TAI Data API",
    description="Enterprise SAP-AI Synchronization API for automated data processing."
)

# --- DATABASE DEPENDENCY ---
def get_db():
    """
    Dependency that creates a new SQLAlchemy Session for each request 
    and ensures it is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        # Yield the session to the path operation function
        yield db
    finally:
        # Close the session to prevent connection leaks
        db.close()

# --- ROUTES ---

@app.get("/", tags=["General"])
def read_root():
    """Returns a basic health check and welcome message."""
    return {"message": "Welcome to TAI Data API", "status": "online"}

@app.get("/sync/sap-to-ai", tags=["Synchronization"])
def sync_data(limit: int = 100, db: Session = Depends(get_db)):
    """
    Trigger the synchronization service to pull data from SAP 
    and push it to the AI schema.
    """
    try:
        # Call the centralized SyncService logic
        stats = SyncService.sync_sap_to_ai(db, limit)
        # Return success with the sync results
        return {"status": "success", "synced_records": stats}
    except Exception as e:
        # Catch unexpected errors and return a 500 error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sap/vendors", response_model=List[dict], tags=["SAP Data"])
def get_sap_vendors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve raw vendor master data from the SAP schema."""
    vendors = db.query(LFA1).offset(skip).limit(limit).all()
    # Map raw models to a simple JSON-friendly dictionary format
    return [{"LIFNR": v.LIFNR, "NAME1": v.NAME1, "COUNTRY": v.COUNTRY} for v in vendors]

@app.get("/ai/vendors", response_model=List[dict], tags=["AI Data"])
def get_ai_vendors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve enriched vendor data (with AI scores) from the AI schema."""
    vendors = db.query(AiVendor).offset(skip).limit(limit).all()
    # Map enriched models to dictionary format
    return [{"LIFNR": v.LIFNR, "NAME1": v.NAME1, "AI_Score": v.AI_Score} for v in vendors]

@app.get("/sap/bulk-purchase", tags=["SAP Data"])
def get_bulk_purchase(limit: int = 10, db: Session = Depends(get_db)):
    """
    Returns Purchase Orders and Line Items in the specific 
    SAP SERVER -> API -> JSON format requested.
    """
    try:
        data = SyncService.get_bulk_purchase_json(db, limit)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- APP STARTUP ---
if __name__ == "__main__":
    # Import uvicorn server only when running as a script
    import uvicorn
    # Start the application on all local interfaces on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
