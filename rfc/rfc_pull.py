#!/usr/bin/env python3
# =============================================================
#  rfc_pull.py - Pull ANY SAP table into PostgreSQL via RFC
#
#  USAGE:
#    python rfc_pull.py MARA              <- All materials
#    python rfc_pull.py LFA1              <- All vendors
#    python rfc_pull.py EKKO              <- Purchase order headers
#    python rfc_pull.py VBAK              <- Sales order headers
#    python rfc_pull.py MARA 10000        <- MARA, max 10000 rows
#    python rfc_pull.py EKKO "BUKRS='1000'"   <- With filter
# =============================================================

import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from rfc_client import SAPRFCClient
from config import PG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rfc.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("RFC-Pull")

# Known primary keys for common SAP tables
# If your table is not here, the first column is used as PK
TABLE_PKS = {
    "MARA":  "matnr",   # Material
    "MARC":  "matnr",   # Material/Plant
    "MARD":  "matnr",   # Storage Location
    "LFA1":  "lifnr",   # Vendor Master
    "LFB1":  "lifnr",   # Vendor per Company
    "KNA1":  "kunnr",   # Customer Master
    "EKKO":  "ebeln",   # Purchase Order Header
    "EKPO":  "ebeln",   # Purchase Order Item
    "VBAK":  "vbeln",   # Sales Order Header
    "VBAP":  "vbeln",   # Sales Order Item
    "BKPF":  "belnr",   # Accounting Doc Header
    "BSEG":  "belnr",   # Accounting Doc Item
    "MKPF":  "mblnr",   # Material Doc Header
    "MSEG":  "mblnr",   # Material Doc Item
    "RBKP":  "belnr",   # Invoice Doc Header
    "RSEG":  "belnr",   # Invoice Doc Item
    "T001":  "bukrs",   # Company Codes
    "T001W": "werks",   # Plants
}


def load_postgres(records, table_name, schema):
    """Load records into PostgreSQL table."""
    if not records:
        log.warning("No records to load.")
        return 0

    columns = list(records[0].keys())

    # Determine primary key
    primary_key = TABLE_PKS.get(table_name.upper(), columns[0])
    if primary_key not in columns:
        # fallback: skip mandt, use next column
        primary_key = columns[1] if columns[0] == "mandt" and len(columns) > 1 else columns[0]

    log.info(f"Primary key: {primary_key}")

    # Filter empty PKs and deduplicate
    seen = set()
    clean = []
    for r in records:
        pk_val = r.get(primary_key, "").strip()
        if pk_val and pk_val not in seen:
            seen.add(pk_val)
            clean.append(r)

    skipped = len(records) - len(clean)
    if skipped:
        log.info(f"Filtered out {skipped} rows (empty/duplicate PK).")
    records = clean

    log.info(f"Connecting to PostgreSQL: {PG['host']}")
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    pg_table = table_name.lower()

    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        cur.execute(f"DROP TABLE IF EXISTS {schema}.{pg_table} CASCADE;")
        conn.commit()

        # Create table (all TEXT)
        col_defs = ", ".join(f"{c} TEXT" for c in columns)
        cur.execute(f"""
            CREATE TABLE {schema}.{pg_table} (
                {col_defs},
                synced_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY ({primary_key})
            );
        """)
        conn.commit()
        log.info(f"Table {schema}.{pg_table} created (PK: {primary_key}).")

        # Upsert
        col_str    = ", ".join(columns)
        val_str    = ", ".join(f"%({c})s" for c in columns)
        update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != primary_key)
        sql = f"""
            INSERT INTO {schema}.{pg_table} ({col_str})
            VALUES ({val_str})
            ON CONFLICT ({primary_key})
            DO UPDATE SET {update_str}, synced_at = NOW();
        """

        total = 0
        for i in range(0, len(records), 1000):
            batch = records[i:i + 1000]
            psycopg2.extras.execute_batch(cur, sql, batch)
            conn.commit()
            total += len(batch)
            log.info(f"  Saved {total}/{len(records)} rows...")

    conn.close()
    return total


def main():
    args     = sys.argv[1:]
    table    = args[0].upper() if args else "MARA"
    max_rows = int(args[1]) if len(args) > 1 and args[1].isdigit() else 50000
    where    = args[1] if len(args) > 1 and not args[1].isdigit() else None
    schema   = PG["schema"]

    log.info("=" * 55)
    log.info(f"RFC TABLE  : {table}")
    log.info(f"PG TABLE   : {schema}.{table.lower()}")
    log.info(f"MAX ROWS   : {max_rows}")
    if where:
        log.info(f"FILTER     : {where}")
    log.info(f"STARTED    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 55)

    try:
        # Connect to SAP via RFC
        client = SAPRFCClient()

        # Read table
        records = client.read_table(table, where=where, max_rows=max_rows)
        client.close()

        if not records:
            log.warning(f"No data returned for table {table}.")
            return

        log.info(f"Fetched {len(records)} rows, {len(records[0])} columns from SAP.")

        # Save to PostgreSQL
        count = load_postgres(records, table, schema)

        log.info("=" * 55)
        log.info(f"SUCCESS! {count} rows synced to {schema}.{table.lower()}")
        log.info("=" * 55)

    except Exception as e:
        log.error(f"FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
