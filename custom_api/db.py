#!/usr/bin/env python3
# =============================================================
#  custom_api/db.py - Database logging for all operations
# =============================================================

import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from config import PG


def setup_tables():
    """Create tracking tables in sap_sap schema."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")

            # Table for all API operations (pull & push)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.api_log (
                    id              SERIAL PRIMARY KEY,
                    operation       TEXT NOT NULL,
                    service_name    TEXT NOT NULL,
                    entity_name     TEXT NOT NULL,
                    mata_id         TEXT,
                    request_payload JSONB,
                    response_data   JSONB,
                    records_count   INTEGER DEFAULT 0,
                    status          TEXT NOT NULL DEFAULT 'PENDING',
                    status_code     INTEGER,
                    error_message   TEXT,
                    called_by       TEXT DEFAULT 'api_user',
                    created_at      TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_api_log_operation
                    ON {schema}.api_log (operation);
                CREATE INDEX IF NOT EXISTS idx_api_log_status
                    ON {schema}.api_log (status);
                CREATE INDEX IF NOT EXISTS idx_api_log_service
                    ON {schema}.api_log (service_name);
                CREATE INDEX IF NOT EXISTS idx_api_log_created
                    ON {schema}.api_log (created_at);
            """)
            conn.commit()
            print(f"Table {schema}.api_log ready!")
    finally:
        conn.close()


def log_operation(operation, service_name, entity_name, mata_id=None,
                  request_payload=None, response_data=None, records_count=0,
                  status="PENDING", status_code=None, error_message=None,
                  called_by="api_user"):
    """Log any API operation (pull or push) to the database."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {schema}.api_log
                    (operation, service_name, entity_name, mata_id,
                     request_payload, response_data, records_count,
                     status, status_code, error_message, called_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                operation, service_name, entity_name, mata_id,
                json.dumps(request_payload) if request_payload else None,
                json.dumps(response_data) if response_data else None,
                records_count, status, status_code, error_message, called_by
            ))
            log_id = cur.fetchone()[0]
            conn.commit()
            return log_id
    finally:
        conn.close()


def save_pulled_data(service_name, entity_name, records):
    """Save pulled records as JSON payloads to sap_data table."""
    if not records:
        return 0

    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor() as cur:
            # Delete old data for this entity
            cur.execute(
                f"DELETE FROM {schema}.sap_data WHERE service_name = %s AND entity_name = %s;",
                (service_name, entity_name)
            )

            rows = []
            for rec in records:
                # Guess unique key
                mata_id = None
                for key in ["Product", "Material", "BusinessPartner", "SalesOrder",
                           "PurchaseOrder", "Supplier", "Customer", "Plant"]:
                    if key in rec and rec[key]:
                        mata_id = str(rec[key]).strip()
                        break
                if not mata_id:
                    for k, v in rec.items():
                        if v is not None and str(v).strip():
                            mata_id = str(v).strip()
                            break

                rows.append((service_name, entity_name, mata_id,
                           json.dumps(rec, ensure_ascii=False)))

            sql = f"""INSERT INTO {schema}.sap_data
                      (service_name, entity_name, mata_id, payload)
                      VALUES (%s, %s, %s, %s::jsonb);"""

            psycopg2.extras.execute_batch(cur, sql, rows)
            conn.commit()
            return len(rows)
    finally:
        conn.close()
