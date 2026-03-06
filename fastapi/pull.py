#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pull.py — Pull data from SAP (Full or Delta) and save to PostgreSQL

USAGE:
    python pull.py           <- smart pull (delta if possible, full if first time)
    python pull.py --full    <- force full pull (ignore last pull time)

EDIT ONLY the section below to control what gets pulled.
"""
import os, json, time, sys
import requests, psycopg2
from dotenv import load_dotenv
from datetime import datetime, timezone
from requests.auth import HTTPBasicAuth
import urllib3; urllib3.disable_warnings()

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ╔══════════════════════════════════════════════════════╗
# ║  EDIT HERE ONLY                                     ║
# ╚══════════════════════════════════════════════════════╝

RECORDS_PER_JOB = 1000   # max records to pull per service

PULL_JOBS = [
    # (Service Name,                      Entity,           Field to filter by for delta)
    ("API_SALES_ORDER_SRV",              "A_SalesOrder",         "LastChangeDate"),
    ("API_PURCHASEORDER_PROCESS_SRV",    "A_PurchaseOrder",      "LastChangeDate"),
    # ("ZFAP_VENDOR_BALANCE_SRV",        "YourEntity",           "ChangedOn"),
    # ("API_PRODUCT_SRV",                "A_Product",            "LastChangeDate"),
]

# ══════════════════════════════════════════════════════════
# DO NOT EDIT BELOW THIS LINE
# ══════════════════════════════════════════════════════════

BATCH_SIZE     = 500
MAX_RETRIES    = 5
SAP_RETRY_WAIT = 10
DB_RETRY_WAIT  = 15

SAP_BASE    = f"{os.getenv('SAP_PROTOCOL','https')}://{os.getenv('SAP_HOST')}:{os.getenv('SAP_PORT')}"
SAP_AUTH    = HTTPBasicAuth(os.getenv("SAP_USER"), os.getenv("SAP_PASSWORD"))
SAP_HEADERS = {"Accept": "application/json", "sap-client": os.getenv("SAP_CLIENT", "100")}
SAP_PREFIX  = "/sap/opu/odata/sap"

DB = dict(host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT","5432")),
          dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))

# Force full pull if --full flag is passed
FORCE_FULL = "--full" in sys.argv


def get_db():
    """Connect to DB with retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return psycopg2.connect(**DB)
        except psycopg2.OperationalError as e:
            print(f"  [DB Retry {attempt}/{MAX_RETRIES}] {e}")
            if attempt < MAX_RETRIES:
                print(f"  Waiting {DB_RETRY_WAIT}s...")
                time.sleep(DB_RETRY_WAIT)
            else: raise


def get_last_pull_time(entity_name):
    """
    Read the last successful pull timestamp for this entity from the DB.
    Returns None if this entity was never pulled before (triggers a full pull).
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pulled_at FROM sap_sap.sap_pull_fastapi
                WHERE entity_name = %s
                ORDER BY pulled_at DESC LIMIT 1;
            """, (entity_name,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def pull(service_path, entity, delta_field=None, since=None):
    """
    Pull records from SAP.
    - If `since` is given: delta pull — only records changed after that time.
    - If `since` is None: full pull — all records.
    """
    url     = f"{SAP_BASE}{service_path}/{entity}"
    session = requests.Session()
    session.auth, session.verify, session.headers = SAP_AUTH, False, SAP_HEADERS

    all_records, skip = [], 0

    # Build delta filter if applicable
    delta_filter = None
    if since and delta_field:
        since_str    = since.strftime("%Y-%m-%dT%H:%M:%S")
        delta_filter = f"{delta_field} gt datetime'{since_str}'"
        print(f"  [DELTA] Only pulling records where {delta_field} > {since_str}")
    else:
        print(f"  [FULL]  Pulling all records (no previous pull found)")

    while len(all_records) < RECORDS_PER_JOB:
        batch  = min(BATCH_SIZE, RECORDS_PER_JOB - len(all_records))
        params = {"$format":"json", "$top":batch, "$skip":skip}
        if delta_filter:
            params["$filter"] = delta_filter

        data = {}
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = session.get(url, params=params, timeout=120)
                resp.raise_for_status()
                data = resp.json().get("d", {})
                break
            except Exception as e:
                print(f"  [Retry {attempt}/{MAX_RETRIES}] {e}")
                if attempt < MAX_RETRIES:
                    print(f"  Waiting {SAP_RETRY_WAIT}s...")
                    time.sleep(SAP_RETRY_WAIT)

        records = [
            {k: v for k, v in r.items() if not k.startswith("__") and not isinstance(v, (dict, list))}
            for r in data.get("results", [])
        ]

        if not records:
            print("  No more records from SAP.")
            break

        all_records.extend(records)
        skip += len(records)
        print(f"  Fetched {len(records)} — Total: {len(all_records)}")

    return all_records


def save(service_path, entity, records, pull_mode):
    """
    Save records to sap_sap.sap_pull_fastapi.
    - Full pull:  replaces the row entirely.
    - Delta pull: merges new records into the existing JSON array.
    """
    conn = get_db()
    now  = datetime.now(timezone.utc)
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS sap_sap;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sap_sap.sap_pull_fastapi (
                    id           SERIAL PRIMARY KEY,
                    service_path TEXT,
                    entity_name  TEXT,
                    payload      JSONB,
                    pull_mode    TEXT,         -- 'full' or 'delta'
                    pulled_at    TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            if pull_mode == "full":
                # Full pull: replace everything
                cur.execute("DELETE FROM sap_sap.sap_pull_fastapi WHERE service_path=%s AND entity_name=%s;",
                            (service_path, entity))
                cur.execute("INSERT INTO sap_sap.sap_pull_fastapi (service_path, entity_name, payload, pull_mode) VALUES (%s,%s,%s::jsonb,%s);",
                            (service_path, entity, json.dumps(records, ensure_ascii=False), "full"))
                print(f"  [FULL]  Replaced all data — {len(records)} records saved.")
            else:
                # Delta pull: append new records to existing array
                cur.execute("""
                    UPDATE sap_sap.sap_pull_fastapi
                    SET payload   = payload || %s::jsonb,
                        pull_mode = 'delta',
                        pulled_at = NOW()
                    WHERE service_path = %s AND entity_name = %s;
                """, (json.dumps(records, ensure_ascii=False), service_path, entity))
                print(f"  [DELTA] Appended {len(records)} new/changed records.")

            conn.commit()
    finally:
        conn.close()


# ── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    mode_label = "FORCE FULL" if FORCE_FULL else "SMART (Delta if possible)"
    print("=" * 55)
    print(f"  SAP PULL — Mode: {mode_label}")
    print(f"  Jobs: {len(PULL_JOBS)} service(s), up to {RECORDS_PER_JOB} records each")
    print("=" * 55)

    for service_name, entity, delta_field in PULL_JOBS:
        service = f"{SAP_PREFIX}/{service_name}"
        print(f"\n  [JOB] {entity}  ({service_name})")

        # Decide: full or delta?
        last_pull = None if FORCE_FULL else get_last_pull_time(entity)
        pull_mode = "full" if last_pull is None else "delta"

        if last_pull:
            print(f"  Last pull: {last_pull.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        records = pull(service, entity, delta_field=delta_field, since=last_pull)

        if records:
            save(service, entity, records, pull_mode)
        else:
            if pull_mode == "delta":
                print(f"  No new/changed records since last pull. DB is up to date.")
            else:
                print(f"  No records returned from SAP.")

    print("\n  All done!")
    print("\n  SQL to view:")
    print("    SELECT entity_name, pull_mode, jsonb_array_length(payload) AS total, pulled_at")
    print("    FROM sap_sap.sap_pull_fastapi;")
