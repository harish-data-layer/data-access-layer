#!/usr/bin/env python3
# =============================================================
#  whole_sap/pull_all.py - Pull ENTIRE SAP OData into PostgreSQL
#
#  This script:
#    1. Discovers ALL OData services via the SAP Catalog
#    2. Gets all entity sets for each service
#    3. Pulls data from every entity set
#    4. Creates tables dynamically in the 'whole_sap' schema
#    5. Loads everything into PostgreSQL
#
#  USAGE:
#    python pull_all.py                  <- pull everything
#    python pull_all.py --discover-only  <- just show what's available
#    python pull_all.py --service API_PRODUCT_SRV  <- pull one service only
#    python pull_all.py --resume         <- resume from last failure
#
# =============================================================

import re
import sys
import json
import logging
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from discover_services import discover_services, discover_entity_sets, create_session, get_base_url
from config import SAP, PG, MAX_RECORDS_PER_ENTITY, PG_BATCH_SIZE, ONLY_SERVICES

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("whole_sap.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("PullAll")


# =============================================================
#  PROGRESS TRACKING
# =============================================================
PROGRESS_FILE = "pull_progress.json"


def load_progress():
    """Load pull progress from file (for --resume)."""
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"completed": [], "failed": [], "started_at": None}


def save_progress(progress):
    """Save pull progress to file."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


# =============================================================
#  PULL DATA FROM A SINGLE ENTITY SET
# =============================================================
def pull_entity_data(session, base_url, service_url, entity_name, max_records=None):
    """
    Pull all records from a single OData entity set.

    Args:
        session:      authenticated requests session
        base_url:     e.g. "https://s1.mncinfosys.com:44329"
        service_url:  service path e.g. "/sap/opu/odata/sap/API_PRODUCT_SRV"
        entity_name:  entity set name e.g. "A_Product"
        max_records:  safety limit

    Returns:
        list of dicts (records)
    """
    if max_records is None:
        max_records = MAX_RECORDS_PER_ENTITY

    # Build full entity URL
    if service_url.startswith("http"):
        entity_url = f"{service_url}/{entity_name}"
    else:
        svc_path = service_url.strip()
        if not svc_path.startswith("/"):
            svc_path = "/" + svc_path
        entity_url = f"{base_url}{svc_path}/{entity_name}"

    all_records = []
    params = {"$format": "json", "$top": 1000}
    page = 1
    url = entity_url

    while url and len(all_records) < max_records:
        log.info(f"    Page {page}: {url[:100]}...")
        try:
            resp = session.get(url, params=params, timeout=SAP["timeout"])

            if resp.status_code == 404:
                log.warning(f"    Entity {entity_name} returned 404 - skipping")
                return all_records
            if resp.status_code == 403:
                log.warning(f"    Entity {entity_name} returned 403 (no auth) - skipping")
                return all_records
            if resp.status_code >= 500:
                log.warning(f"    Entity {entity_name} returned {resp.status_code} - skipping")
                return all_records

            resp.raise_for_status()

            data    = resp.json().get("d", {})
            results = data.get("results", [])

            # Some entities return data directly (not in 'results')
            if not results and isinstance(data, list):
                results = data

            all_records.extend(results)
            log.info(f"    Got {len(results)} records (total: {len(all_records)})")

            # Follow pagination
            url    = data.get("__next") if isinstance(data, dict) else None
            params = {}
            page  += 1

        except requests.exceptions.Timeout:
            log.warning(f"    Timeout on page {page} - continuing with {len(all_records)} records")
            break
        except Exception as e:
            log.error(f"    Pull error on page {page}: {e}")
            break

    return all_records


# =============================================================
#  CLEAN RECORDS
# =============================================================
def clean_records(records):
    """
    Clean OData records for PostgreSQL insertion.
    - Remove __metadata, __deferred internal fields
    - Normalize column names to lowercase
    - Skip nested objects
    """
    cleaned = []
    for r in records:
        row = {}
        for key, val in r.items():
            if key.startswith("__"):
                continue
            col = key.strip().lower().replace("/", "_").replace(" ", "_")
            # Make sure column name is valid PostgreSQL identifier
            col = re.sub(r'[^a-z0-9_]', '_', col)
            if not col:
                continue
            if isinstance(val, dict):
                continue  # skip nested objects/navigation properties
            if isinstance(val, list):
                continue  # skip arrays
            row[col] = str(val).strip() if val is not None else ""
        if row:
            cleaned.append(row)
    return cleaned


# =============================================================
#  SAVE TO POSTGRESQL
# =============================================================
def save_to_postgres(table_name, records):
    """
    Create table dynamically and insert records into the whole_sap schema.

    Args:
        table_name:  name of the table to create (entity set name sanitized)
        records:     list of cleaned dicts
    """
    if not records:
        log.warning(f"    No records to save for {table_name}")
        return 0

    schema = PG["schema"]

    # Sanitize table name for PostgreSQL
    safe_table = re.sub(r'[^a-z0-9_]', '_', table_name.lower())
    if not safe_table:
        log.error(f"    Invalid table name: {table_name}")
        return 0

    columns = list(records[0].keys())
    if not columns:
        return 0

    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )

    try:
        with conn.cursor() as cur:
            # Ensure schema exists
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
            conn.commit()

            # Drop existing table and recreate
            cur.execute(f'DROP TABLE IF EXISTS {schema}."{safe_table}" CASCADE;')
            conn.commit()

            # All columns as TEXT (safest for mixed OData data)
            col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
            cur.execute(f"""
                CREATE TABLE {schema}."{safe_table}" (
                    {col_defs},
                    _synced_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
            log.info(f"    Table {schema}.{safe_table} created ({len(columns)} columns)")

            # Insert in batches
            col_str = ", ".join(f'"{c}"' for c in columns)
            val_str = ", ".join(f"%({c})s" for c in columns)
            sql = f'INSERT INTO {schema}."{safe_table}" ({col_str}) VALUES ({val_str});'

            total = 0
            for i in range(0, len(records), PG_BATCH_SIZE):
                batch = records[i:i + PG_BATCH_SIZE]
                try:
                    psycopg2.extras.execute_batch(cur, sql, batch)
                    conn.commit()
                    total += len(batch)
                except Exception as e:
                    conn.rollback()
                    log.error(f"    Batch insert error: {e}")
                    # Try individual inserts for this batch
                    for rec in batch:
                        try:
                            cur.execute(sql, rec)
                            conn.commit()
                            total += 1
                        except Exception:
                            conn.rollback()
                            pass

            log.info(f"    Saved {total}/{len(records)} rows to {schema}.{safe_table}")
            return total

    finally:
        conn.close()


# =============================================================
#  MAIN PULL LOGIC
# =============================================================
def pull_all(discover_only=False, service_filter=None, resume=False):
    """
    Main function to pull the entire SAP database via OData.

    Args:
        discover_only:   if True, just list services/entities without pulling
        service_filter:  if set, only pull this specific service
        resume:          if True, skip already-completed entities
    """
    start_time = datetime.now()
    log.info("=" * 70)
    log.info("  WHOLE SAP OData Pull")
    log.info(f"  Server   : {SAP['host']}:{SAP['port']}")
    log.info(f"  Schema   : {PG['schema']}")
    log.info(f"  Started  : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 70)

    # Step 1: Discover all services
    log.info("\n[STEP 1] Discovering all OData services...")
    services = discover_services()

    if not services:
        log.error("No services found! Ensure OData is activated on SAP.")
        return

    # Filter services if needed
    if service_filter:
        services = [s for s in services if service_filter.upper() in s["technical_name"].upper()]
        log.info(f"Filtered to {len(services)} services matching '{service_filter}'")

    if ONLY_SERVICES:
        services = [s for s in services if s["technical_name"] in ONLY_SERVICES]
        log.info(f"Filtered to {len(services)} services from ONLY_SERVICES config")

    # Step 2: Discover entities for each service
    log.info(f"\n[STEP 2] Discovering entity sets for {len(services)} services...")
    service_entities = []
    for svc in services:
        svc_url = svc.get("service_url", "")
        if not svc_url:
            continue
        entities = discover_entity_sets(svc_url)
        if entities:
            service_entities.append({
                "service": svc,
                "entities": entities,
            })

    # Count totals
    total_entities = sum(len(se["entities"]) for se in service_entities)
    log.info(f"\nDiscovered {len(service_entities)} services with {total_entities} entity sets total")

    if discover_only:
        print(f"\n{'='*80}")
        print(f"  DISCOVERY COMPLETE: {len(service_entities)} services, {total_entities} entities")
        print(f"{'='*80}")
        for se in service_entities:
            svc = se["service"]
            print(f"\n  {svc['technical_name']}:")
            for ent in se["entities"]:
                print(f"    - {ent}")
        return

    # Load resume progress
    progress = load_progress() if resume else {"completed": [], "failed": [], "started_at": start_time.isoformat()}
    if not progress.get("started_at"):
        progress["started_at"] = start_time.isoformat()

    # Step 3: Create schema
    log.info(f"\n[STEP 3] Ensuring schema '{PG['schema']}' exists...")
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG['schema']};")
        conn.commit()
    conn.close()

    # Step 4: Pull data from every entity
    log.info(f"\n[STEP 4] Pulling data from {total_entities} entity sets...")
    session  = create_session()
    base_url = get_base_url()

    stats = {
        "services_processed": 0,
        "entities_pulled": 0,
        "entities_skipped": 0,
        "entities_failed": 0,
        "total_rows": 0,
        "tables_created": 0,
    }

    for se in service_entities:
        svc = se["service"]
        svc_name = svc["technical_name"]
        svc_url  = svc["service_url"]

        log.info(f"\n{'─'*60}")
        log.info(f"SERVICE: {svc_name} ({len(se['entities'])} entities)")
        log.info(f"{'─'*60}")

        for entity_name in se["entities"]:
            # Build unique key for progress tracking
            entity_key = f"{svc_name}/{entity_name}"

            # Skip if already done (resume mode)
            if resume and entity_key in progress["completed"]:
                log.info(f"  [{entity_name}] Already completed - skipping")
                stats["entities_skipped"] += 1
                continue

            log.info(f"\n  [{entity_name}] Pulling...")

            try:
                # Pull data
                records = pull_entity_data(session, base_url, svc_url, entity_name)

                if records:
                    # Clean records
                    cleaned = clean_records(records)

                    if cleaned:
                        # Create table name: service_entity  (e.g. api_product_srv_a_product)
                        table_name = f"{svc_name}_{entity_name}".lower()

                        # Save to PostgreSQL
                        rows_saved = save_to_postgres(table_name, cleaned)
                        stats["total_rows"] += rows_saved
                        stats["tables_created"] += 1
                    else:
                        log.info(f"    No clean data for {entity_name}")
                else:
                    log.info(f"    No records returned for {entity_name}")

                stats["entities_pulled"] += 1
                progress["completed"].append(entity_key)

            except Exception as e:
                log.error(f"    FAILED: {entity_name} - {e}")
                stats["entities_failed"] += 1
                progress["failed"].append({"entity": entity_key, "error": str(e)})

            # Save progress after each entity
            save_progress(progress)

        stats["services_processed"] += 1

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    log.info("\n" + "=" * 70)
    log.info("  PULL COMPLETE - SUMMARY")
    log.info("=" * 70)
    log.info(f"  Duration           : {duration}")
    log.info(f"  Services processed : {stats['services_processed']}")
    log.info(f"  Entities pulled    : {stats['entities_pulled']}")
    log.info(f"  Entities skipped   : {stats['entities_skipped']}")
    log.info(f"  Entities failed    : {stats['entities_failed']}")
    log.info(f"  Total rows saved   : {stats['total_rows']}")
    log.info(f"  Tables created     : {stats['tables_created']}")
    log.info(f"  Target schema      : {PG['schema']}")
    log.info("=" * 70)

    # Save final stats
    progress["finished_at"] = end_time.isoformat()
    progress["stats"] = stats
    save_progress(progress)


# =============================================================
#  CLI
# =============================================================
def main():
    args = sys.argv[1:]

    discover_only  = "--discover-only" in args
    resume         = "--resume" in args
    service_filter = None

    if "--service" in args:
        idx = args.index("--service")
        if idx + 1 < len(args):
            service_filter = args[idx + 1]

    if "--help" in args or "-h" in args:
        print("""
Usage: python pull_all.py [OPTIONS]

Options:
  --discover-only     List all services and entities without pulling data
  --service NAME      Pull only the service matching NAME
  --resume            Resume from last interrupted pull
  -h, --help          Show this help message

Examples:
  python pull_all.py                              # Pull everything
  python pull_all.py --discover-only              # Just list what's available
  python pull_all.py --service API_PRODUCT_SRV    # Pull one service
  python pull_all.py --resume                     # Resume interrupted pull
        """)
        return

    pull_all(
        discover_only=discover_only,
        service_filter=service_filter,
        resume=resume,
    )


if __name__ == "__main__":
    main()
