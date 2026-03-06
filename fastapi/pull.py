#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pull.py — Pull data from SAP and save to PostgreSQL

USAGE:
    python pull.py

EDIT ONLY the section below to control what gets pulled.
Everything else is automatic.
"""
import os, json, time
import requests, psycopg2
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import urllib3; urllib3.disable_warnings()

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ╔══════════════════════════════════════════════════════╗
# ║  EDIT HERE ONLY — Add services you want to pull     ║
# ╚══════════════════════════════════════════════════════╝

RECORDS_PER_JOB = 1000          # Pull this many records from every service below

PULL_JOBS = [
    # (Service Name,                         Entity to Pull)
    ("API_SALES_ORDER_SRV",               "A_SalesOrder"),
    ("API_PURCHASEORDER_PROCESS_SRV",     "A_PurchaseOrder"),
    # To add a new service, just copy the line above and change the names:
    # ("ZFAP_VENDOR_BALANCE_SRV",         "YourEntityName"),
    # ("API_PRODUCT_SRV",                 "A_Product"),
]

# ══════════════════════════════════════════════════════════
# DO NOT EDIT BELOW THIS LINE
# ══════════════════════════════════════════════════════════

# Retry settings
BATCH_SIZE       = 500   # records per SAP request
MAX_RETRIES      = 5     # how many times to retry on failure
SAP_RETRY_WAIT   = 10    # seconds gap between SAP retries
DB_RETRY_WAIT    = 15    # seconds gap between DB connection retries

# SAP connection (from .env)
SAP_BASE    = f"{os.getenv('SAP_PROTOCOL','https')}://{os.getenv('SAP_HOST')}:{os.getenv('SAP_PORT')}"
SAP_AUTH    = HTTPBasicAuth(os.getenv("SAP_USER"), os.getenv("SAP_PASSWORD"))
SAP_HEADERS = {"Accept": "application/json", "sap-client": os.getenv("SAP_CLIENT", "100")}
SAP_PREFIX  = "/sap/opu/odata/sap"

# DB connection (from .env)
DB = dict(host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT","5432")),
          dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))


def pull(service_path, entity, total):
    """Pull all records from a SAP service entity."""
    url     = f"{SAP_BASE}{service_path}/{entity}"
    session = requests.Session()
    session.auth, session.verify, session.headers = SAP_AUTH, False, SAP_HEADERS

    all_records, skip = [], 0
    print(f"\n  Pulling up to {total} records from: {entity}")

    while len(all_records) < total:
        batch = min(BATCH_SIZE, total - len(all_records))
        data  = {}

        # Try fetching — retry up to MAX_RETRIES times with a gap
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = session.get(url, params={"$format":"json","$top":batch,"$skip":skip}, timeout=120)
                resp.raise_for_status()
                data = resp.json().get("d", {})
                break
            except Exception as e:
                print(f"  [Retry {attempt}/{MAX_RETRIES}] Error: {e}")
                if attempt < MAX_RETRIES:
                    print(f"  Waiting {SAP_RETRY_WAIT}s before next retry...")
                    time.sleep(SAP_RETRY_WAIT)

        # Remove SAP internal metadata from each record
        records = [
            {k: v for k, v in r.items() if not k.startswith("__") and not isinstance(v, (dict, list))}
            for r in data.get("results", [])
        ]

        if not records:
            print("  SAP has no more records. Stopping.")
            break

        all_records.extend(records)
        skip += len(records)
        print(f"  Fetched {len(records)} records — Total so far: {len(all_records)}")

    return all_records


def save(service_path, entity, records):
    """Save all records as a single JSON array row in the database."""
    # Connect to DB — retry with a gap if busy
    conn = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = psycopg2.connect(**DB); break
        except psycopg2.OperationalError as e:
            print(f"  [DB Retry {attempt}/{MAX_RETRIES}] {e}")
            if attempt < MAX_RETRIES:
                print(f"  Waiting {DB_RETRY_WAIT}s...")
                time.sleep(DB_RETRY_WAIT)
            else: raise

    with conn:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS sap_sap;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sap_sap.sap_pull_fastapi (
                    id           SERIAL PRIMARY KEY,
                    service_path TEXT,
                    entity_name  TEXT,
                    payload      JSONB,          -- all records as a JSON array
                    pulled_at    TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            # Replace old data with fresh pull
            cur.execute("DELETE FROM sap_sap.sap_pull_fastapi WHERE service_path=%s AND entity_name=%s;",
                        (service_path, entity))
            cur.execute("INSERT INTO sap_sap.sap_pull_fastapi (service_path, entity_name, payload) VALUES (%s,%s,%s::jsonb);",
                        (service_path, entity, json.dumps(records, ensure_ascii=False)))
    conn.close()
    print(f"  Saved {len(records)} records to sap_sap.sap_pull_fastapi")


# Run all jobs
if __name__ == "__main__":
    print("=" * 55)
    print(f"  Running {len(PULL_JOBS)} pull job(s)... ({RECORDS_PER_JOB} records each)")
    print("=" * 55)

    for service_name, entity in PULL_JOBS:
        service = f"{SAP_PREFIX}/{service_name}"
        print(f"\n  [JOB] {entity}  ({service_name})")
        records = pull(service, entity, RECORDS_PER_JOB)
        if records:
            save(service, entity, records)
        else:
            print(f"  No records returned for {entity}.")

    print("\n  All done!")
    print("\n  SQL to view in pgAdmin:")
    print("    SELECT entity_name, jsonb_array_length(payload) AS total, pulled_at")
    print("    FROM sap_sap.sap_pull_fastapi;")
