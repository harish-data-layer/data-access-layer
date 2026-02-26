#!/usr/bin/env python3
# =============================================================
#  whole_sap/pull_payload.py
#
#  Pull SAP OData data and store as JSON PAYLOAD in PostgreSQL.
#
#  Instead of creating separate columns for each field,
#  this stores the ENTIRE record as a JSON payload:
#
#    id  |  entity_name  |  mata_id (unique key)  |  payload (JSON)
#    1   |  A_Product    |  MAT001                |  {"Product":"MAT001","Type":"ROH",...}
#    2   |  A_Product    |  MAT002                |  {"Product":"MAT002","Type":"HALB",...}
#
#  USAGE:
#    python pull_payload.py                              # Pull default services
#    python pull_payload.py ZAPI_SALES_ORDER_SRV         # Pull 1 service
#    python pull_payload.py SALES_ORDER PRODUCT          # Keywords
#
# =============================================================

import sys
import json
import logging
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from discover_services import discover_services, discover_entity_sets, create_session, get_base_url
from config import SAP, PG, MAX_RECORDS_PER_ENTITY

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
log = logging.getLogger("PullPayload")


# =============================================================
#  SERVICES TO PULL (edit this list)
# =============================================================
SELECTED_SERVICES = [
    "ZAPI_SALES_ORDER_SRV",
    "ZMD_C_PRODUCT_MAINTAIN_SRV",
    "ZMD_PRODUCT_HIERARCHY_SRV",
    "ZMDG_MATERIAL_SRV",
    "ZMDG_BP_SRV",
    "ZMDG_CUSTOMER_GENIL_SRV",
    "ZSD_SALES_ORDER_IMPORT",
    # Add more services here...
]


# =============================================================
#  TABLE SETUP - Create the payload table
# =============================================================
TABLE_NAME = "sap_data"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {schema}.{table} (
    id              SERIAL PRIMARY KEY,
    service_name    TEXT NOT NULL,
    entity_name     TEXT NOT NULL,
    mata_id         TEXT,
    payload         JSONB NOT NULL,
    synced_at       TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_{table}_entity
    ON {schema}.{table} (entity_name);

CREATE INDEX IF NOT EXISTS idx_{table}_mata_id
    ON {schema}.{table} (mata_id);

CREATE INDEX IF NOT EXISTS idx_{table}_service
    ON {schema}.{table} (service_name);

-- GIN index for searching inside JSON payload
CREATE INDEX IF NOT EXISTS idx_{table}_payload
    ON {schema}.{table} USING GIN (payload);
"""


def setup_table():
    """Create the payload table and indexes in whole_sap schema."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
            conn.commit()

            sql = CREATE_TABLE_SQL.format(schema=schema, table=TABLE_NAME)
            cur.execute(sql)
            conn.commit()
            log.info(f"✅ Table {schema}.{TABLE_NAME} ready")
    finally:
        conn.close()


# =============================================================
#  SMART SERVICE MATCHING
# =============================================================
def match_services(selected, all_services):
    """Match selected service names against catalog (exact, partial, keyword)."""
    matched = []
    not_found = []

    for sel in selected:
        sel_upper = sel.upper()
        found = False

        # 1. Exact match
        for svc in all_services:
            if svc["technical_name"].upper() == sel_upper:
                if svc not in matched:
                    matched.append(svc)
                found = True
                break

        if found:
            continue

        # 2. Partial match
        for svc in all_services:
            if sel_upper in svc["technical_name"].upper():
                if svc not in matched:
                    matched.append(svc)
                found = True

        if found:
            continue

        # 3. Keyword match
        keywords = [k for k in sel_upper.split("_") if len(k) > 2]
        for svc in all_services:
            name = svc["technical_name"].upper()
            if all(kw in name for kw in keywords):
                if svc not in matched:
                    matched.append(svc)
                found = True

        if not found:
            not_found.append(sel)

    return matched, not_found


# =============================================================
#  PULL ENTITY DATA
# =============================================================
def pull_entity_data(session, base_url, service_url, entity_name, max_records=None):
    """Pull all records from a single OData entity set."""
    if max_records is None:
        max_records = MAX_RECORDS_PER_ENTITY

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
        log.info(f"    Page {page}: pulling...")
        try:
            resp = session.get(url, params=params, timeout=SAP["timeout"])

            if resp.status_code in (404, 403) or resp.status_code >= 500:
                log.warning(f"    Entity {entity_name} returned {resp.status_code} - skipping")
                return all_records

            resp.raise_for_status()

            data    = resp.json().get("d", {})
            results = data.get("results", [])

            if not results and isinstance(data, list):
                results = data

            all_records.extend(results)
            log.info(f"    Got {len(results)} records (total: {len(all_records)})")

            url    = data.get("__next") if isinstance(data, dict) else None
            params = {}
            page  += 1

        except requests.exceptions.Timeout:
            log.warning(f"    Timeout on page {page}")
            break
        except Exception as e:
            log.error(f"    Pull error: {e}")
            break

    return all_records


# =============================================================
#  CLEAN PAYLOAD - remove OData internal fields
# =============================================================
def clean_payload(record):
    """
    Clean a single OData record:
    - Remove __metadata, __deferred etc.
    - Remove nested objects (navigation properties)
    - Keep all actual data fields
    Returns: cleaned dict (the payload)
    """
    clean = {}
    for key, val in record.items():
        if key.startswith("__"):
            continue
        if isinstance(val, dict):
            continue
        if isinstance(val, list):
            continue
        clean[key] = val
    return clean


def guess_unique_key(record):
    """
    Try to guess the unique ID (mata_id) from the record.
    SAP OData entities usually have the first field as the key.
    Common patterns: Product, BusinessPartner, SalesOrder, PurchaseOrder, etc.
    """
    # Common SAP key field names (in order of priority)
    key_candidates = [
        "Product", "Material", "MATNR",
        "BusinessPartner", "Supplier", "Customer", "LIFNR", "KUNNR",
        "SalesOrder", "VBELN",
        "PurchaseOrder", "EBELN",
        "Plant", "WERKS",
        "CompanyCode", "BUKRS",
    ]

    for key_name in key_candidates:
        if key_name in record and record[key_name]:
            return str(record[key_name]).strip()

    # Fallback: use the first non-empty field value
    for key, val in record.items():
        if key.startswith("__"):
            continue
        if isinstance(val, (dict, list)):
            continue
        if val is not None and str(val).strip():
            return str(val).strip()

    return None


# =============================================================
#  SAVE PAYLOADS TO POSTGRESQL
# =============================================================
def save_payloads(service_name, entity_name, records):
    """
    Save records as JSON payloads into the sap_data table.

    Each record becomes one row:
      id | service_name | entity_name | mata_id | payload (JSON) | synced_at
    """
    if not records:
        return 0

    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )

    try:
        with conn.cursor() as cur:
            # Delete old data for this entity (fresh sync)
            cur.execute(
                f"DELETE FROM {schema}.{TABLE_NAME} WHERE service_name = %s AND entity_name = %s;",
                (service_name, entity_name)
            )
            conn.commit()

            # Prepare rows
            rows = []
            for record in records:
                payload = clean_payload(record)
                if not payload:
                    continue
                mata_id = guess_unique_key(record)
                rows.append((
                    service_name,
                    entity_name,
                    mata_id,
                    json.dumps(payload, ensure_ascii=False),
                ))

            if not rows:
                return 0

            # Batch insert
            sql = f"""
                INSERT INTO {schema}.{TABLE_NAME}
                    (service_name, entity_name, mata_id, payload)
                VALUES (%s, %s, %s, %s::jsonb);
            """

            total = 0
            batch_size = 500
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                try:
                    psycopg2.extras.execute_batch(cur, sql, batch)
                    conn.commit()
                    total += len(batch)
                except Exception as e:
                    conn.rollback()
                    log.error(f"    Batch error: {e}")
                    # Try one by one
                    for row in batch:
                        try:
                            cur.execute(sql, row)
                            conn.commit()
                            total += 1
                        except Exception:
                            conn.rollback()

            log.info(f"    ✅ Saved {total} payloads for {entity_name}")
            return total

    finally:
        conn.close()


# =============================================================
#  MAIN
# =============================================================
def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print("""
Usage: python pull_payload.py [SERVICE1] [SERVICE2] ...

Pulls SAP data and stores each record as a JSON payload.

Table structure in PostgreSQL (whole_sap.sap_data):
  id            | SERIAL       | Auto-increment ID
  service_name  | TEXT         | e.g. ZAPI_SALES_ORDER_SRV
  entity_name   | TEXT         | e.g. A_SalesOrder
  mata_id       | TEXT         | Unique SAP key (auto-detected)
  payload       | JSONB        | Full record as JSON
  synced_at     | TIMESTAMP    | When it was pulled

Examples:
  python pull_payload.py                                    # Pull default services
  python pull_payload.py ZAPI_SALES_ORDER_SRV               # Pull 1 service
  python pull_payload.py ZAPI_SALES_ORDER_SRV ZMDG_BP_SRV   # Pull 2 services
  python pull_payload.py SALES_ORDER PRODUCT                 # Keyword match

Query examples in pgAdmin:
  SELECT * FROM whole_sap.sap_data WHERE entity_name = 'A_SalesOrder';
  SELECT mata_id, payload->>'SalesOrder' FROM whole_sap.sap_data WHERE entity_name = 'A_SalesOrder';
  SELECT * FROM whole_sap.sap_data WHERE payload->>'Product' = 'MAT001';
        """)
        return

    # Get services
    if args:
        selected = list(args)
    else:
        selected = list(SELECTED_SERVICES)

    start_time = datetime.now()
    log.info("=" * 70)
    log.info("  SAP OData PAYLOAD Pull")
    log.info(f"  Server   : {SAP['host']}:{SAP['port']}")
    log.info(f"  Schema   : {PG['schema']}")
    log.info(f"  Table    : {TABLE_NAME}")
    log.info(f"  Format   : JSON Payload (id, mata_id, payload)")
    log.info(f"  Services : {len(selected)}")
    for s in selected:
        log.info(f"    → {s}")
    log.info(f"  Started  : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 70)

    # Step 1: Setup table
    log.info("\n[STEP 1] Setting up payload table...")
    setup_table()

    # Step 2: Discover services
    log.info("\n[STEP 2] Discovering services from SAP catalog...")
    all_services = discover_services()

    if not all_services:
        log.error("No services found!")
        return

    # Step 3: Match services
    matched, not_found = match_services(selected, all_services)

    if not_found:
        log.warning(f"\n⚠️  Not found: {not_found}")
        for nf in not_found:
            keywords = [k for k in nf.upper().split("_") if len(k) > 2]
            suggestions = [s["technical_name"] for s in all_services
                          if any(kw in s["technical_name"].upper() for kw in keywords)][:5]
            if suggestions:
                log.info(f"  Similar to '{nf}': {suggestions}")

    if not matched:
        log.error("No services matched!")
        return

    log.info(f"\n[STEP 3] Matched {len(matched)} services:")
    for svc in matched:
        log.info(f"  ✓ {svc['technical_name']}")

    # Step 4: Pull and store
    log.info(f"\n[STEP 4] Pulling data as JSON payloads...")
    session  = create_session()
    base_url = get_base_url()

    total_entities = 0
    total_payloads = 0

    for svc in matched:
        svc_name = svc["technical_name"]
        svc_url  = svc["service_url"]

        log.info(f"\n{'━'*60}")
        log.info(f"  SERVICE: {svc_name}")
        log.info(f"{'━'*60}")

        entities = discover_entity_sets(svc_url)
        log.info(f"  Found {len(entities)} entity sets")

        if not entities:
            continue

        for entity_name in entities:
            log.info(f"\n  📥 [{entity_name}] Pulling...")

            try:
                records = pull_entity_data(session, base_url, svc_url, entity_name)

                if records:
                    count = save_payloads(svc_name, entity_name, records)
                    total_payloads += count
                    total_entities += 1
                else:
                    log.info(f"    Empty - 0 records")

            except Exception as e:
                log.error(f"    ❌ FAILED: {e}")

    # Summary
    end_time = datetime.now()
    duration = end_time - start_time

    log.info("\n" + "=" * 70)
    log.info("  ✅ PAYLOAD PULL COMPLETE")
    log.info("=" * 70)
    log.info(f"  Duration       : {duration}")
    log.info(f"  Services       : {len(matched)}")
    log.info(f"  Entities       : {total_entities}")
    log.info(f"  Total payloads : {total_payloads}")
    log.info(f"  Schema         : {PG['schema']}")
    log.info(f"  Table          : {PG['schema']}.{TABLE_NAME}")
    log.info("=" * 70)
    log.info("")
    log.info("  Query your data in pgAdmin:")
    log.info(f"    SELECT * FROM {PG['schema']}.{TABLE_NAME};")
    log.info(f"    SELECT mata_id, payload FROM {PG['schema']}.{TABLE_NAME} WHERE entity_name = 'A_SalesOrder';")
    log.info("")


if __name__ == "__main__":
    main()
