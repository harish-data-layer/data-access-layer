#!/usr/bin/env python3
# =============================================================
#  push_back/db_setup.py
#
#  Creates the push_sap table in sap_sap schema
#  (right next to the sap_data table)
#
#  Table: sap_sap.push_sap
#  Tracks every push operation - what was pushed, status, errors
# =============================================================

import psycopg2
from config import PG

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {schema}.push_sap (
    id              SERIAL PRIMARY KEY,

    -- What is being pushed
    service_name    TEXT NOT NULL,
    entity_name     TEXT NOT NULL,
    mata_id         TEXT,
    action          TEXT NOT NULL DEFAULT 'CREATE',

    -- The data (JSON payload from AI team)
    request_payload JSONB NOT NULL,
    response_data   JSONB,

    -- Status tracking
    status          TEXT NOT NULL DEFAULT 'PENDING',
    status_code     INTEGER,
    error_message   TEXT,

    -- Who & When
    pushed_by       TEXT DEFAULT 'ai_team',
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_push_sap_status
    ON {schema}.push_sap (status);

CREATE INDEX IF NOT EXISTS idx_push_sap_entity
    ON {schema}.push_sap (entity_name);

CREATE INDEX IF NOT EXISTS idx_push_sap_mata_id
    ON {schema}.push_sap (mata_id);

CREATE INDEX IF NOT EXISTS idx_push_sap_pushed_by
    ON {schema}.push_sap (pushed_by);

CREATE INDEX IF NOT EXISTS idx_push_sap_created_at
    ON {schema}.push_sap (created_at);

CREATE INDEX IF NOT EXISTS idx_push_sap_payload
    ON {schema}.push_sap USING GIN (request_payload);
"""


def setup():
    """Create the push_sap table."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
            conn.commit()
            cur.execute(CREATE_TABLE_SQL.format(schema=schema))
            conn.commit()
            print(f"Table {schema}.push_sap ready!")
    finally:
        conn.close()


if __name__ == "__main__":
    setup()
