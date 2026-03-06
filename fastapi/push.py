#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push.py — Push changed/new records from your DB back to SAP

USAGE:
    python push.py

HOW IT WORKS:
    1. Reads records from sap_sap.sap_push_queue table in your DB
    2. For each record:
       - If action = "create" → POST to SAP (create new record)
       - If action = "update" → PATCH to SAP (update existing record)
    3. Marks each record as "done" or "failed" after the attempt

HOW TO ADD RECORDS TO THE QUEUE (SQL example):
    INSERT INTO sap_sap.sap_push_queue
        (service_path, entity_name, action, key_field, key_value, payload)
    VALUES
        ('/sap/opu/odata/sap/API_SALES_ORDER_SRV', 'A_SalesOrder',
         'update', 'SalesOrder', '1000001',
         '{"RequestedDeliveryDate": "2026-04-01", "PurchaseOrderByCustomer": "PO-999"}');
"""
import os, json, time
import requests, psycopg2
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import urllib3; urllib3.disable_warnings()

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ══════════════════════════════════════════════════════════
# DO NOT EDIT — all config comes from .env
# ══════════════════════════════════════════════════════════

MAX_RETRIES    = 5
SAP_RETRY_WAIT = 10
DB_RETRY_WAIT  = 15

SAP_BASE    = f"{os.getenv('SAP_PROTOCOL','https')}://{os.getenv('SAP_HOST')}:{os.getenv('SAP_PORT')}"
SAP_AUTH    = HTTPBasicAuth(os.getenv("SAP_USER"), os.getenv("SAP_PASSWORD"))
SAP_HEADERS = {"Accept": "application/json", "Content-Type": "application/json",
               "sap-client": os.getenv("SAP_CLIENT", "100")}

DB = dict(host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT","5432")),
          dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))


def get_db():
    """Connect to DB with retry."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return psycopg2.connect(**DB)
        except psycopg2.OperationalError as e:
            print(f"  [DB Retry {attempt}/{MAX_RETRIES}] {e}")
            if attempt < MAX_RETRIES:
                time.sleep(DB_RETRY_WAIT)
            else: raise


def setup_push_queue():
    """Create the push queue table if it doesn't exist."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS sap_sap;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sap_sap.sap_push_queue (
                    id           SERIAL PRIMARY KEY,
                    service_path TEXT NOT NULL,       -- e.g. /sap/opu/odata/sap/API_SALES_ORDER_SRV
                    entity_name  TEXT NOT NULL,       -- e.g. A_SalesOrder
                    action       TEXT NOT NULL,       -- 'create' or 'update'
                    key_field    TEXT,                -- field that identifies the record (e.g. SalesOrder)
                    key_value    TEXT,                -- value of the key field (e.g. '1000001')
                    payload      JSONB NOT NULL,      -- the fields to create/update
                    status       TEXT DEFAULT 'pending',   -- pending / done / failed
                    sap_response TEXT,                -- SAP response message
                    queued_at    TIMESTAMPTZ DEFAULT NOW(),
                    pushed_at    TIMESTAMPTZ
                );
            """)
            conn.commit()
        print("  Push queue table ready: sap_sap.sap_push_queue")
    finally:
        conn.close()


def get_csrf_token(session, service_path):
    """Get CSRF token from SAP — required before any write operation."""
    url = f"{SAP_BASE}{service_path}"
    try:
        resp = session.get(url, headers={"x-csrf-token": "Fetch"}, timeout=30)
        token = resp.headers.get("x-csrf-token")
        cookies = resp.cookies
        return token, cookies
    except Exception as e:
        print(f"  [CSRF] Failed to fetch CSRF token: {e}")
        return None, None


def push_to_sap(session, service_path, entity_name, action, key_field, key_value, payload, csrf_token, cookies):
    """
    Push one record to SAP.
    - action='create' → POST
    - action='update' → PATCH (only sends the fields in payload)
    Returns (success: bool, message: str)
    """
    headers = {**SAP_HEADERS, "x-csrf-token": csrf_token}

    if action == "create":
        url  = f"{SAP_BASE}{service_path}/{entity_name}"
        resp = session.post(url, json=payload, headers=headers, cookies=cookies, timeout=120)
    elif action == "update":
        # PATCH to the specific record key
        url  = f"{SAP_BASE}{service_path}/{entity_name}('{key_value}')"
        resp = session.patch(url, json=payload, headers=headers, cookies=cookies, timeout=120)
    else:
        return False, f"Unknown action '{action}'"

    if resp.status_code in (200, 201, 204):
        return True, f"HTTP {resp.status_code} OK"
    else:
        return False, f"HTTP {resp.status_code}: {resp.text[:300]}"


def run_push():
    """Process all pending records in sap_push_queue and push to SAP."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Fetch all pending records
            cur.execute("""
                SELECT id, service_path, entity_name, action, key_field, key_value, payload
                FROM sap_sap.sap_push_queue
                WHERE status = 'pending'
                ORDER BY queued_at ASC;
            """)
            rows = cur.fetchall()

        if not rows:
            print("  No pending records in push queue. Nothing to push.")
            return

        print(f"  Found {len(rows)} pending record(s) to push to SAP.")

        # Group by service_path to minimise CSRF token requests
        session = requests.Session()
        session.auth, session.verify = SAP_AUTH, False

        csrf_cache = {}   # cache CSRF tokens per service
        results = {"done": 0, "failed": 0}

        for row in rows:
            record_id, service_path, entity_name, action, key_field, key_value, payload = row
            print(f"\n  [PUSH] ID={record_id} | {action.upper()} | {entity_name} | key={key_value}")

            # Get a cached CSRF token for this service
            if service_path not in csrf_cache:
                token, cookies = get_csrf_token(session, service_path)
                csrf_cache[service_path] = (token, cookies)
            token, cookies = csrf_cache[service_path]

            if not token:
                msg = "Could not get CSRF token from SAP"
                status = "failed"
            else:
                success = False
                msg     = ""
                # Retry with gap
                for attempt in range(1, MAX_RETRIES + 1):
                    success, msg = push_to_sap(session, service_path, entity_name,
                                               action, key_field, key_value, payload, token, cookies)
                    if success:
                        break
                    print(f"  [Retry {attempt}/{MAX_RETRIES}] {msg}")
                    if attempt < MAX_RETRIES:
                        print(f"  Waiting {SAP_RETRY_WAIT}s...")
                        time.sleep(SAP_RETRY_WAIT)

                status = "done" if success else "failed"

            # Update status in queue
            conn2 = get_db()
            try:
                with conn2.cursor() as cur2:
                    cur2.execute("""
                        UPDATE sap_sap.sap_push_queue
                        SET status='%s', sap_response=%%s, pushed_at=NOW()
                        WHERE id=%%s;
                    """ % status, (msg, record_id))
                    conn2.commit()
            finally:
                conn2.close()

            print(f"  [{status.upper()}] {msg}")
            results[status] = results.get(status, 0) + 1

        print(f"\n  Push complete — Done: {results.get('done',0)} | Failed: {results.get('failed',0)}")

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 55)
    print("  SAP PUSH — Processing push queue")
    print("=" * 55)

    setup_push_queue()
    run_push()

    print(f"\n  SQL to view push queue:")
    print(f"    SELECT id, entity_name, action, key_value, status, sap_response, pushed_at")
    print(f"    FROM sap_sap.sap_push_queue")
    print(f"    ORDER BY queued_at DESC;")
