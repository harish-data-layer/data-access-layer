#!/usr/bin/env python3
# =============================================================
#  odata_pull.py - Pull SAP data via OData API into PostgreSQL
#
#  USAGE:
#    python odata_pull.py material       <- Pull materials (MARA)
#    python odata_pull.py vendor         <- Pull vendors (LFA1)
#    python odata_pull.py sales_order    <- Pull sales orders
#    python odata_pull.py purchase_order <- Pull purchase orders
#    python odata_pull.py test           <- Just test connectivity
#
#  REQUIRES: OData services enabled on SAP server
# =============================================================

import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from sap_odata_client import SAPODataClient
from config import SERVICES, ENTITIES, PG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("odata.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("OData-Pull")


def pull_and_sync(data_type):
    """
    Pull data from SAP OData API and sync to PostgreSQL.

    Args:
        data_type: one of 'material', 'vendor', 'sales_order', 'purchase_order'
    """
    if data_type not in SERVICES:
        log.error(f"Unknown data type: {data_type}")
        log.info(f"Available: {list(SERVICES.keys())}")
        sys.exit(1)

    service_path = SERVICES[data_type]
    entity       = ENTITIES[data_type]
    pg_table     = data_type  # e.g. 'material', 'vendor'

    log.info("=" * 55)
    log.info(f"DATA TYPE  : {data_type}")
    log.info(f"OData Path : {service_path}")
    log.info(f"Entity     : {entity}")
    log.info(f"PG Table   : {PG['schema']}.{pg_table}")
    log.info(f"STARTED    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 55)

    # Step 1: Pull from SAP
    client  = SAPODataClient()
    records = client.pull(service_path, entity)
    log.info(f"Pulled {len(records)} records from SAP OData.")

    if not records:
        log.warning("No records returned. Nothing to sync.")
        return

    # Step 2: Clean records (remove OData metadata)
    clean_records = []
    for r in records:
        clean = {}
        for key, val in r.items():
            if key.startswith("__"):  # skip __metadata, __deferred
                continue
            # Clean column name for PostgreSQL
            col = key.strip().lower().replace("/", "_")
            # Handle value
            if isinstance(val, dict):
                continue  # skip nested objects
            clean[col] = str(val).strip() if val is not None else ""
        if clean:
            clean_records.append(clean)

    log.info(f"Cleaned: {len(clean_records)} records, {len(clean_records[0])} columns")

    # Step 3: Load into PostgreSQL
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )

    schema  = PG["schema"]
    columns = list(clean_records[0].keys())

    # Use first column as primary key
    primary_key = columns[0]

    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        cur.execute(f"DROP TABLE IF EXISTS {schema}.{pg_table} CASCADE;")
        conn.commit()

        # All TEXT columns
        col_defs = ", ".join(f"{c} TEXT" for c in columns)
        cur.execute(f"""
            CREATE TABLE {schema}.{pg_table} (
                {col_defs},
                synced_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY ({primary_key})
            );
        """)
        conn.commit()
        log.info(f"Table {schema}.{pg_table} ready.")

        # Insert
        col_str = ", ".join(columns)
        val_str = ", ".join(f"%({c})s" for c in columns)
        sql = f"INSERT INTO {schema}.{pg_table} ({col_str}) VALUES ({val_str});"

        # Filter out empty PKs
        valid = [r for r in clean_records if r.get(primary_key, "").strip()]
        log.info(f"Inserting {len(valid)} rows (skipped {len(clean_records) - len(valid)} empty PKs)")

        total = 0
        for i in range(0, len(valid), 500):
            batch = valid[i:i + 500]
            psycopg2.extras.execute_batch(cur, sql, batch)
            conn.commit()
            total += len(batch)
            log.info(f"  Saved {total}/{len(valid)} rows...")

    conn.close()

    log.info("=" * 55)
    log.info(f"SUCCESS! {total} rows synced to {schema}.{pg_table}")
    log.info("=" * 55)


def test_connection():
    """Test OData connectivity without pulling data."""
    log.info("Testing SAP OData connectivity...")
    client = SAPODataClient()

    for name, path in SERVICES.items():
        log.info(f"\n--- {name.upper()} ---")
        try:
            url = client._find_active_url(path)
            log.info(f"  CONNECTED: {url}")
        except ConnectionError:
            log.warning(f"  FAILED: Cannot reach {path}")
        client.active_url = None  # reset for next test


def main():
    args = sys.argv[1:]
    data_type = args[0].lower() if args else "test"

    if data_type == "test":
        test_connection()
    else:
        pull_and_sync(data_type)


if __name__ == "__main__":
    main()
