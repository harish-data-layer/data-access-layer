import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, JSON

from .models import SapExtraction
from .sap_client import fetch_from_sap

# ==============================================================================
# 1. High-Performance Upsert Logic (The Magic Merging Feature)
# ==============================================================================
def sync_sap_to_db(db: Session, entity: str, records: list, is_delta: bool):
    """
    Moves SAP data into Postgres safely and fast. 
    If a record already exists, it intelligently updates it. If not, it creates it.
    """
    if not records:
        return

    # Step A: Prepare a standard INSERT statement
    stmt = insert(SapExtraction).values(
        entity_name=entity,
        payload=records,
        last_sync=func.now()
    )

    # Step B: Tell Postgres what to do if the 'entity_name' already exists (ON CONFLICT)
    if is_delta:
        # It's a DELTA pull: We only fetched NEW records.
        # So we APPEND them (add them to the end) of our existing JSON array.
        # '||' is the PostgreSQL operator to concatenate JSONB.
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['entity_name'],
            set_={
                "payload": SapExtraction.payload.cast(JSON).concat(records),
                "last_sync": func.now()
            }
        )
    else:
        # It's a FULL pull: OVERWRITE whatever was in the database with this fresh data.
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['entity_name'],
            set_={
                "payload": records,
                "last_sync": func.now()
            }
        )

    # Step C: Execute the raw query using SQLAlchemy's safe runner
    db.execute(upsert_stmt)
    db.commit()


# ==============================================================================
# 2. The Background Worker (Controls the flow)
# ==============================================================================
def run_sync_worker(db: Session, service_name: str, entity: str, delta_field: str, force_full: bool = False, custom_since: datetime = None, max_records: int = 1000):
    """
    1. Checks when we last pulled data.
    2. Downloads new data from SAP using fetch_from_sap.
    3. Saves it to DB using our Upsert logic above.
    """
    start_time = time.time()
    print(f"\n[WORKER] Starting job for: {entity}")

    # Step A: Figure out if this is a FULL pull or a DELTA pull
    if custom_since:
        last_sync = custom_since
        is_delta = True
    elif force_full:
        last_sync = None
        is_delta = False
    else:
        # Ask Database for the last sync time
        record = db.query(SapExtraction.last_sync).filter(SapExtraction.entity_name == entity).first()
        last_sync = record[0] if record else None
        is_delta = last_sync is not None

    # PRINT THE MODE FIRST (As requested)
    print(f"  PULL MODE: {'DELTA' if is_delta else 'FULL'}")

    try:
        # Step B: Call SAP API to download the data
        records = fetch_from_sap(service_name, entity, delta_field, last_sync, max_records)

        if records is None:
            # This happens if the client encountered a fatal error and we want to stop
            return

        if not records:
            print("  Nothing new from SAP. Database is already up to date!")
            return

        # Step C: Save to PostgreSQL
        sync_sap_to_db(db, entity, records, is_delta)
        
        elapsed = time.time() - start_time
        print(f"  Saved {len(records)} records beautifully in {elapsed:.2f} seconds!")

    except Exception as e:
        print(f"  [ERROR] Something went wrong with {entity}: {e}")
        db.rollback()
