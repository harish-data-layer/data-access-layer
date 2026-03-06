import time
import sys
import argparse
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from hybrid_orm.database import get_db, SessionLocal, Base, engine
from hybrid_orm.sync import run_sync_worker

# ==============================================================================
# 1. Configuration (Add your SAP services here)
# ==============================================================================
PULL_JOBS = [
    # Format: (Service Name, Entity Name, Delta Date Field)
    ("API_SALES_ORDER_SRV", "A_SalesOrder", "LastChangeDate"),
    ("API_PURCHASEORDER_PROCESS_SRV", "A_PurchaseOrder", "LastChangeDate"),
    ("ZFAP_VENDOR_BALANCE_SRV", "VendorBalanceSet", "ChangedOn"),
    ("ZFAP_VENDOR_LINE_ITEMS_SRV", "VendorLineItemSet", "ChangedOn"),
    ("ZOAA_VENDOR_STOCK_SRV", "VendorStockSet", "LastChangeDate"),
]
MAX_RECORDS = 1000

# ==============================================================================
# 2. FastAPI Setup (For API triggers)
# ==============================================================================
app = FastAPI(title="SAP Hybrid ORM API")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.post("/pull/{entity_name}")
async def trigger_pull(entity_name: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """API endpoint to start a background sync instantly."""
    job = next((j for j in PULL_JOBS if j[1] == entity_name), None)
    if not job: 
        return {"error": f"Entity '{entity_name}' not found in PULL_JOBS list."}
    
    background_tasks.add_task(run_sync_worker, db, job[0], job[1], job[2], max_records=MAX_RECORDS)
    return {"message": f"Background sync started beautifully for {entity_name}."}

# ==============================================================================
# 3. Terminal CLI (For manual or scheduled runs)
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Force wipe and pull everything")
    parser.add_argument("--since", type=str, help="Custom date e.g. 2026-03-01T08:00:00")
    args = parser.parse_args()

    custom_since = None
    if args.since:
        try:
            custom_since = datetime.fromisoformat(args.since)
        except ValueError:
            print("[ERROR] Date must be YYYY-MM-DDTHH:MM:SS format.")
            sys.exit(1)

    print("\n" + "=" * 50)
    print("  SAP Hybrid ORM Puller (Terminal)")
    print("=" * 50)
    
    with SessionLocal() as db:
        for service, entity, delta_field in PULL_JOBS:
            run_sync_worker(db, service, entity, delta_field, args.full, custom_since, MAX_RECORDS)
