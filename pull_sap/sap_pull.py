#!/usr/bin/env python3
# =============================================================
#  sap_pull.py - Pull ANY SAP table into PostgreSQL
#  Uses SAP GUI Scripting (grid reading - proven to work)
#
#  USAGE:
#    python sap_pull.py MARA        <- Materials
#    python sap_pull.py LFA1        <- Vendor Master
#    python sap_pull.py VBAK        <- Sales Orders
#    python sap_pull.py MARA 2000   <- MARA with max 2000 rows
# =============================================================

import sys
import os
import time
import logging
import win32com.client
import psycopg2
import psycopg2.extras
from datetime import datetime

# =============================================================
#  SETTINGS
# =============================================================

PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "tai_data_api_db",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

# =============================================================
#  LOGGING (no emojis - fixes Windows cp1252 crash)
# =============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sap_pull.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

# =============================================================
#  STEP 1 - Connect to open SAP GUI session
# =============================================================

def get_sap_session():
    log.info("Connecting to SAP GUI...")
    try:
        sap  = win32com.client.GetObject("SAPGUI")
        app  = sap.GetScriptingEngine
        conn = app.Children(0)
        sess = conn.Children(0)
        log.info("Connected to SAP GUI session OK.")
        return sess
    except Exception as e:
        log.error(f"Cannot connect to SAP GUI: {e}")
        log.error("Make sure SAP GUI is open and logged in!")
        raise

# =============================================================
#  STEP 2 - Navigate SE16N, execute, read grid
# =============================================================

def pull_table(session, table: str, max_rows: int) -> list:
    log.info(f"Opening SE16N for table: {table}")

    # Go to SE16N
    session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
    session.findById("wnd[0]").sendVKey(0)
    time.sleep(2)

    # Close popup if one appears
    try:
        if session.ActiveWindow.Name != "wnd[0]":
            session.ActiveWindow.sendVKey(0)
            time.sleep(1)
    except:
        pass

    # Enter table name
    session.findById("wnd[0]/usr/ctxtGD-TAB").text = table
    time.sleep(1)

    # Set max rows
    try:
        session.findById("wnd[0]/usr/txtGD-MAX_LINES").text = str(max_rows)
        log.info(f"Max rows set to: {max_rows}")
    except:
        log.warning("Could not set max rows field")

    # Execute (F8)
    log.info("Executing query (F8)...")
    session.findById("wnd[0]").sendVKey(8)
    time.sleep(5)

    # Find Grid control
    grid = None
    grid_ids = [
        "wnd[0]/shellcont/shell",
        "wnd[0]/usr/cntlRESULT_LIST/shellcont/shell",
        "wnd[0]/usr/cntlGRID1/shellcont/shell",
        "wnd[0]/usr/cntlCUSTOM/shellcont/shell",
        "wnd[0]/usr/cntlALV_GRID/shellcont/shell",
        "wnd[0]/usr/cntlCONTAINER/shellcont/shell",
    ]

    for attempt in range(3):
        for gid in grid_ids:
            try:
                grid = session.findById(gid)
                log.info(f"Grid found: {gid}")
                break
            except:
                pass
        if grid:
            break
        log.info(f"Grid not found yet, retrying ({attempt+1}/3)...")
        time.sleep(5)

    if not grid:
        log.error("Could not find data grid on screen!")
        raise RuntimeError("Grid not found - did the query return results?")

    total_rows = grid.RowCount
    col_names  = grid.ColumnOrder
    rows_to_read = min(total_rows, max_rows)

    log.info(f"Found {total_rows} rows, {len(col_names)} columns in SAP.")
    log.info(f"Will read {rows_to_read} rows...")
    log.info(f"Columns: {list(col_names)[:10]}...")

    # Read all rows - everything as TEXT (no float conversion)
    # SAP grids lazy-load data. We must scroll the grid to force rows to load.
    records = []
    visible_rows = grid.VisibleRowCount  # how many rows the grid shows at once
    log.info(f"Grid visible rows per page: {visible_rows}")

    chunk_size = max(visible_rows - 1, 20)  # scroll by this many rows at a time

    for chunk_start in range(0, rows_to_read, chunk_size):
        # Scroll grid to this chunk position to force lazy-load
        try:
            grid.firstVisibleRow = chunk_start
            time.sleep(0.3)  # give SAP time to load
        except:
            try:
                grid.setCurrentCell(chunk_start, col_names[0])
                time.sleep(0.3)
            except:
                pass

        chunk_end = min(chunk_start + chunk_size, rows_to_read)
        for i in range(chunk_start, chunk_end):
            row = {}
            for col in col_names:
                val = grid.GetCellValue(i, col)
                clean_col = str(col).strip().lower().replace("/", "_")
                row[clean_col] = str(val).strip() if val else ""
            records.append(row)

        if chunk_end % 200 == 0 or chunk_end == rows_to_read:
            log.info(f"  ...read {chunk_end}/{rows_to_read} rows")

    log.info(f"Extraction complete: {len(records)} rows read.")
    return records

# =============================================================
#  STEP 3 - Load into PostgreSQL (all TEXT columns)
# =============================================================

def load_postgres(records: list, pg_table: str) -> int:
    if not records:
        log.warning("No records to load.")
        return 0

    # Force lowercase table name so pgAdmin shows it properly
    pg_table = pg_table.lower()

    log.info(f"Connecting to PostgreSQL: {PG['host']}")
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )

    columns = list(records[0].keys())

    # Skip 'mandt' (client) column for primary key if present
    if len(columns) > 1 and columns[0] == "mandt":
        primary_key = columns[1]
    else:
        primary_key = columns[0]

    # Filter out rows with empty primary key and deduplicate
    seen_keys = set()
    clean_records = []
    for r in records:
        pk_val = r.get(primary_key, "").strip()
        if pk_val and pk_val not in seen_keys:
            seen_keys.add(pk_val)
            clean_records.append(r)

    skipped = len(records) - len(clean_records)
    if skipped > 0:
        log.info(f"Filtered out {skipped} rows (empty/duplicate PK).")
    records = clean_records

    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS real_sap;")

        # Drop old table and recreate with real SAP data
        cur.execute(f'DROP TABLE IF EXISTS real_sap.{pg_table} CASCADE;')
        conn.commit()

        # Create table (all TEXT, lowercase unquoted)
        col_defs = ", ".join(f'{c} TEXT' for c in columns)
        create_sql = f"""
            CREATE TABLE real_sap.{pg_table} (
                {col_defs},
                synced_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY ({primary_key})
            );
        """
        cur.execute(create_sql)
        conn.commit()
        log.info(f"Table real_sap.{pg_table} ready (PK: {primary_key}).")

        # Insert (no conflict - fresh table)
        col_str    = ", ".join(c for c in columns)
        val_str    = ", ".join(f"%({c})s" for c in columns)
        sql = f"""
            INSERT INTO real_sap.{pg_table} ({col_str})
            VALUES ({val_str});
        """

        total = 0
        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            psycopg2.extras.execute_batch(cur, sql, batch)
            conn.commit()
            total += len(batch)
            log.info(f"  Saved {total}/{len(records)} rows...")

    conn.close()
    log.info(f"DONE! {total} rows loaded into real_sap.{pg_table}")
    return total

# =============================================================
#  MAIN
# =============================================================

def main():
    args     = sys.argv[1:]
    table    = args[0].upper() if args else "MARA"
    max_rows = int(args[1]) if len(args) > 1 else 5000
    pg_table = table.lower()

    log.info("=" * 55)
    log.info(f"SAP TABLE  : {table}")
    log.info(f"PG TABLE   : real_sap.{pg_table}")
    log.info(f"MAX ROWS   : {max_rows}")
    log.info(f"STARTED    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 55)

    try:
        session = get_sap_session()
        records = pull_table(session, table, max_rows)
        count   = load_postgres(records, pg_table)

        log.info("=" * 55)
        log.info(f"SUCCESS! {count} rows synced to real_sap.{pg_table}")
        log.info("Open pgAdmin > Schemas > real_sap > Tables to view data!")
        log.info("=" * 55)

    except Exception as e:
        log.error(f"FAILED: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
