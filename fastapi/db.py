#!/usr/bin/env python3
# =============================================================
#  fastapi/db.py - Database Layer
#
#  Manages PostgreSQL schema: fastapi
#  Tables:
#    - fastapi.incoming_requests  → every request AI team sends
#    - fastapi.validation_errors  → every rejected request + reason
# =============================================================

import os
import uuid
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

log = logging.getLogger("FastAPI-DB")

# ─── DB Config ───────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "4.240.80.20"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME", "tai_data_api_db"),
    "user":     os.getenv("DB_USER", "postgres_admin"),
    "password": os.getenv("DB_PASSWORD", ""),
}

SCHEMA = "fastapi"


def get_conn():
    """Get a new DB connection."""
    return psycopg2.connect(**DB_CONFIG)


# =============================================================
#  INIT - Create schema + tables if not exist
# =============================================================
def init_db():
    """
    Create the 'fastapi' schema and all required tables.
    Safe to call multiple times (uses IF NOT EXISTS).
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Create schema
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")

            # Table 1: incoming_requests
            # Stores EVERY request from the AI team
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {SCHEMA}.incoming_requests (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    request_id      UUID NOT NULL UNIQUE,
                    received_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    source_ip       TEXT,
                    payload         JSONB,
                    status          TEXT DEFAULT 'pending',
                    sap_response    JSONB,
                    processed_at    TIMESTAMP WITH TIME ZONE,
                    invoice_number  TEXT,
                    vendor_id       TEXT,
                    total_amount    NUMERIC(15,2),
                    currency        TEXT,
                    called_by       TEXT
                );
            """)

            # Indexes for faster queries
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_fastapi_requests_status
                ON {SCHEMA}.incoming_requests(status);
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_fastapi_requests_invoice
                ON {SCHEMA}.incoming_requests(invoice_number);
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_fastapi_requests_received
                ON {SCHEMA}.incoming_requests(received_at DESC);
            """)

            # Table 2: validation_errors
            # Stores every rejected/failed request + WHY it was rejected
            # This is our "golden error schema" as per requirements
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {SCHEMA}.validation_errors (
                    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    request_id      UUID NOT NULL,
                    error_code      TEXT NOT NULL,
                    error_message   TEXT,
                    field_name      TEXT,
                    rejected_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    raw_payload     JSONB,
                    FOREIGN KEY (request_id)
                        REFERENCES {SCHEMA}.incoming_requests(request_id)
                        ON DELETE CASCADE
                );
            """)

            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_fastapi_errors_request
                ON {SCHEMA}.validation_errors(request_id);
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_fastapi_errors_code
                ON {SCHEMA}.validation_errors(error_code);
            """)

            conn.commit()
            log.info(f"✅ Schema '{SCHEMA}' and tables initialized successfully")
            
        # Also initialize the sap_pull_fastapi table in the sap_sap schema
        init_sap_pull_table()

    except Exception as e:
        conn.rollback()
        log.error(f"❌ DB init failed: {e}")
        raise
    finally:
        conn.close()


# =============================================================
#  STORE REQUEST - Save incoming AI team request
# =============================================================
def store_request(
    request_id: str,
    source_ip: str,
    payload: dict,
    status: str = "pending",
    sap_response: Optional[dict] = None
):
    """
    Insert or update a request in fastapi.incoming_requests.
    Called twice: once on receipt (status=processing), once after SAP call.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Extract useful fields from payload for quick querying
            invoice_number = payload.get("invoice_number")
            vendor_id      = payload.get("vendor_id")
            total_amount   = payload.get("total_amount")
            currency       = payload.get("currency")
            called_by      = payload.get("called_by", "ai_team")

            cur.execute(f"""
                INSERT INTO {SCHEMA}.incoming_requests
                    (request_id, source_ip, payload, status, sap_response,
                     processed_at, invoice_number, vendor_id, total_amount,
                     currency, called_by)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (request_id) DO UPDATE SET
                    status       = EXCLUDED.status,
                    sap_response = EXCLUDED.sap_response,
                    processed_at = EXCLUDED.processed_at;
            """, (
                request_id,
                source_ip,
                json.dumps(payload),
                status,
                json.dumps(sap_response) if sap_response else None,
                datetime.utcnow() if status in ("success", "failed", "local_test") else None,
                invoice_number,
                vendor_id,
                total_amount,
                currency,
                called_by,
            ))
            conn.commit()
            log.info(f"💾 Request {request_id} stored | status={status}")
    except Exception as e:
        conn.rollback()
        log.error(f"❌ Failed to store request {request_id}: {e}")
    finally:
        conn.close()


# =============================================================
#  STORE ERROR - Save rejection/validation error
# =============================================================
def store_error(
    request_id: str,
    error_code: str,
    error_message: str,
    field_name: Optional[str] = None,
    raw_payload: Optional[dict] = None
):
    """
    Insert into fastapi.validation_errors.
    This is our "golden error schema" - stores what was rejected and why.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {SCHEMA}.validation_errors
                    (request_id, error_code, error_message, field_name, raw_payload)
                VALUES
                    (%s, %s, %s, %s, %s);
            """, (
                request_id,
                error_code,
                error_message,
                field_name,
                json.dumps(raw_payload) if raw_payload else None,
            ))
            conn.commit()
            log.info(f"⚠️  Error logged | request={request_id} | code={error_code}")
    except Exception as e:
        conn.rollback()
        log.error(f"❌ Failed to store error for request {request_id}: {e}")
    finally:
        conn.close()


# =============================================================
#  READ - Fetch requests
# =============================================================
def get_all_requests(status: Optional[str] = None, limit: int = 50) -> list:
    """Fetch requests from fastapi.incoming_requests."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = f"SELECT * FROM {SCHEMA}.incoming_requests WHERE 1=1"
            params = []
            if status:
                query += " AND status = %s"
                params.append(status)
            query += " ORDER BY received_at DESC LIMIT %s"
            params.append(str(limit))

            cur.execute(query, params)
            rows = cur.fetchall()

            # Serialize datetimes and uuids
            result = []
            for row in rows:
                r = dict(row)
                for k, v in r.items():
                    if isinstance(v, datetime):
                        r[k] = v.isoformat()
                    elif isinstance(v, uuid.UUID):
                        r[k] = str(v)
                result.append(r)
            return result
    except Exception as e:
        log.error(f"❌ Failed to fetch requests: {e}")
        return []
    finally:
        conn.close()


# =============================================================
#  READ - Fetch errors
# =============================================================
def get_all_errors(limit: int = 50) -> list:
    """Fetch errors from fastapi.validation_errors."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT e.*, r.source_ip, r.invoice_number, r.status as request_status
                FROM {SCHEMA}.validation_errors e
                LEFT JOIN {SCHEMA}.incoming_requests r ON r.request_id = e.request_id
                ORDER BY e.rejected_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()

            result = []
            for row in rows:
                r = dict(row)
                for k, v in r.items():
                    if isinstance(v, datetime):
                        r[k] = v.isoformat()
                    elif isinstance(v, uuid.UUID):
                        r[k] = str(v)
                result.append(r)
            return result
    finally:
        conn.close()


# =============================================================
#  SAP FASTAPI PULL TABLE
# =============================================================
def init_sap_pull_table():
    """Create the table sap_sap.sap_pull_fastapi if not exists."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS sap_sap;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sap_sap.sap_pull_fastapi (
                    id SERIAL PRIMARY KEY,
                    service_path TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    pulled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_sap_pull_fastapi_entity 
                ON sap_sap.sap_pull_fastapi(entity_name);
            """)
            conn.commit()
            log.info("✅ 'sap_sap.sap_pull_fastapi' table initialized")
    except Exception as e:
        conn.rollback()
        log.error(f"❌ Failed to create sap_pull_fastapi table: {e}")
    finally:
        conn.close()

def save_fastapi_pulled_data(service_path: str, entity_name: str, payload: list):
    """Save pulled records as a single JSON array to sap_sap.sap_pull_fastapi"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Delete old record so it replaces it with the freshest one
            cur.execute(
                "DELETE FROM sap_sap.sap_pull_fastapi WHERE service_path = %s AND entity_name = %s;",
                (service_path, entity_name)
            )
            cur.execute("""
                INSERT INTO sap_sap.sap_pull_fastapi (service_path, entity_name, payload)
                VALUES (%s, %s, %s::jsonb);
            """, (service_path, entity_name, json.dumps(payload, ensure_ascii=False)))
            conn.commit()
            log.info(f"💾 Pulled data saved to sap_sap.sap_pull_fastapi for {entity_name}")
    except Exception as e:
        conn.rollback()
        log.error(f"❌ Failed to save pulled data to sap_pull_fastapi for {entity_name}: {e}")
    finally:
        conn.close()

