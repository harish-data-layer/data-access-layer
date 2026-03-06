import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, JSON

from .models import SapExtraction
from .sap_client import fetch_from_sap

def run_sync_worker(db: Session, service: str, entity: str, delta_field: str, force_full: bool = False, custom_since: datetime = None, max_records: int = 1000):
    """
    The Orchestrator:
    1. Sets the date (Full vs Delta)
    2. Pulls data from SAP
    3. High-Speed Upserts into Postgres
    """
    start_time = time.time()
    print(f"\n[WORKER] Starting: {entity}")

    try:
        # 1. Figure out our pull date (DELTA vs FULL)
        last_sync = custom_since
        if not force_full and not custom_since:
            record = db.query(SapExtraction.last_sync).filter(SapExtraction.entity_name == entity).first()
            if record:
                last_sync = record[0]

        print(f"  PULL MODE: {'DELTA' if last_sync else 'FULL'}")

        # 2. Get Data from SAP native client
        records = fetch_from_sap(service, entity, delta_field, last_sync, max_records)
        if not records:
            print("  ✅ Complete: Database is completely up to date. No new records.")
            return

        # 3. High-Speed Postgres UPSERT (Insert or Update seamlessly)
        stmt = insert(SapExtraction).values(entity_name=entity, payload=records, last_sync=func.now())
        
        if last_sync:
            # DELTA mode: APPEND the new JSON batch correctly
            upsert = stmt.on_conflict_do_update(
                index_elements=['entity_name'],
                set_={"payload": SapExtraction.payload.cast(JSON).concat(records), "last_sync": func.now()}
            )
        else:
            # FULL mode: OVERWRITE everything for this entity natively
            upsert = stmt.on_conflict_do_update(
                index_elements=['entity_name'],
                set_={"payload": records, "last_sync": func.now()}
            )

        db.execute(upsert)
        db.commit()
        
        print(f"  ✅ Complete {entity}: Saved {len(records)} records in {time.time() - start_time:.2f} seconds!")

    except Exception as e:
        print(f"  ❌ [ERROR] Failed on {entity}: {e}")
        db.rollback()
