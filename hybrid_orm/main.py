import sys
import argparse
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from hybrid_orm.database import get_db, Base, engine
from hybrid_orm.sync import run_sync_worker

# ==============================================================================
# 1. Easy Configuration (Type your SAP services here)
# ==============================================================================
# Format: ("Service Name", "Entity Name", "Delta Date Field")
PULL_JOBS = [
    # (Service Name,                      Entity Name,           Delta Date Field)
    ("API_SALES_ORDER_SRV",              "A_SalesOrder",         "LastChangeDate"),
    ("API_PURCHASEORDER_PROCESS_SRV",    "A_PurchaseOrder",      "LastChangeDate"),
    ("ZFAP_VENDOR_BALANCE_SRV",          "VendorBalanceSet",      "ChangedOn"),
    ("ZFAP_VENDOR_LINE_ITEMS_SRV",       "VendorLineItemSet",     "ChangedOn"),
    ("ZOAA_VENDOR_STOCK_SRV",            "VendorStockSet",        "LastChangeDate"),
]
MAX_RECORDS = 1000  # How many records to pull in total per job

# ==============================================================================
# 2. FastAPI Setup (For sending commands via HTTP)
# ==============================================================================
# This creates the actual web server API
app = FastAPI(title="SAP Auto-Sync API")

# When the server starts, make sure our database tables exist!
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.post("/pull/{entity_name}")
async def trigger_sap_pull(entity_name: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    When someone hits this API, it tells FastAPI to start the pull in the background.
    The user gets an instant "Success" response, so they don't have to wait.
    """
    # Step A: Check if the entity they asked for exists in our configuration list
    job = next((j for j in PULL_JOBS if j[1] == entity_name), None)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown entity name. Please add it to PULL_JOBS.")
    
    service_name, entity, delta_field = job

    # Step B: Add the heavy lifting to 'background_tasks' so it runs silently
    background_tasks.add_task(
        run_sync_worker, 
        db=db, 
        service_name=service_name, 
        entity=entity, 
        delta_field=delta_field, 
        max_records=MAX_RECORDS
    )
    
    return {"status": "accepted", "message": f"Sync for {entity_name} started silently in the background!"}

# ==============================================================================
# 3. CLI Setup (For running directly from your terminal)
# ==============================================================================
def run_cli():
    """
    This lets you run the script directly like: 
    python -m hybrid_orm.main --full
    """
    print("=" * 50)
    print("  SAP Data Puller started via Terminal")
    print("=" * 50)
    
    # Listen for terminal commands like --full or --since
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Force wipe and pull everything")
    parser.add_argument("--since", type=str, help="e.g. 2026-03-01T08:00:00")
    args = parser.parse_args()
    
    # Attach a custom date if they provided one
    custom_since = None
    if args.since:
        try:
            custom_since = datetime.fromisoformat(args.since)
        except ValueError:
            print("[ERROR] Invalid date format. Type it like: YYYY-MM-DDTHH:MM:SS")
            sys.exit(1)

    # Open a database connection and go through every job!
    with next(get_db()) as db:
        for service_name, entity, delta_field in PULL_JOBS:
            run_sync_worker(
                db=db,
                service_name=service_name,
                entity=entity,
                delta_field=delta_field,
                force_full=args.full,
                custom_since=custom_since,
                max_records=MAX_RECORDS
            )

# This magically runs the CLI function IF we ran this file directly from terminal
if __name__ == "__main__":
    run_cli()
