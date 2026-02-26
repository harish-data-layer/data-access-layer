#!/usr/bin/env python3
# =============================================================
#  whole_sap/pull_selected.py
#
#  Pull SELECTED SAP OData services into PostgreSQL.
#  Just add the services you want in the list below and run!
#
#  USAGE:
#    python pull_selected.py
#
#  OR pass services as arguments:
#    python pull_selected.py API_PRODUCT_SRV API_BUSINESS_PARTNER API_SALES_ORDER_SRV
#
# =============================================================

import re
import sys
import json
import logging
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from discover_services import discover_services, discover_entity_sets, create_session, get_base_url
from config import SAP, PG, MAX_RECORDS_PER_ENTITY, PG_BATCH_SIZE

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
log = logging.getLogger("PullSelected")


# =============================================================
#  LIST YOUR SERVICES HERE
#  Add or remove services as needed.
#
#  NOTE: Your SAP server uses Z-prefixed names. You can use
#  either the full name or a keyword - the script will match!
#
#  To see ALL available services, run:
#    python discover_services.py --save
# =============================================================
SELECTED_SERVICES = [
    # --- These are the ACTUAL names from your SAP catalog ---
    "ZAPI_SALES_ORDER_SRV",           # Sales Orders
    "ZMD_C_PRODUCT_MAINTAIN_SRV",     # Product/Material Master
    "ZMD_PRODUCT_HIERARCHY_SRV",      # Product Hierarchy
    "ZMDG_MATERIAL_SRV",              # Material (MDG)
    "ZMDG_BP_SRV",                    # Business Partner (MDG)
    "ZMDG_CUSTOMER_GENIL_SRV",        # Customer
    "ZSD_SALES_ORDER_IMPORT",         # Sales Order Import
    # "ZMDG_FINANCIALS",              # Financials
    # "ZUI_CFINRPLDPURCHASEORDER",    # Purchase Orders
    # "ZPP_PROCESS_ORDER_MANAGE_SRV", # Process Orders
    # Add more services here...
]


# =============================================================
#  SMART SERVICE MATCHING
# =============================================================
def match_services(selected, all_services):
    """
    Smart matching: tries exact match, then partial match, then keyword match.
    This way you can pass 'PRODUCT' or 'API_PRODUCT_SRV' or 'ZMD_C_PRODUCT_MAINTAIN_SRV'
    and it will find the right service.
    """
    matched = []
    not_found = []

    for sel in selected:
        sel_upper = sel.upper()
        found = False

        # 1. Exact match (e.g., ZAPI_SALES_ORDER_SRV)
        for svc in all_services:
            if svc["technical_name"].upper() == sel_upper:
                if svc not in matched:
                    matched.append(svc)
                found = True
                break

        if found:
            continue

        # 2. Partial match - sel is contained in the name (e.g., API_SALES_ORDER matches ZAPI_SALES_ORDER_SRV)
        for svc in all_services:
            if sel_upper in svc["technical_name"].upper():
                if svc not in matched:
                    matched.append(svc)
                found = True

        if found:
            continue

        # 3. Keyword match - split sel by _ and check if ALL keywords exist in name
        keywords = [k for k in sel_upper.split("_") if len(k) > 2]  # skip short words like SRV, API
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
#  PULL DATA FROM A SINGLE ENTITY SET
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
            log.warning(f"    Timeout on page {page} - got {len(all_records)} records so far")
            break
        except Exception as e:
            log.error(f"    Pull error: {e}")
            break

    return all_records


# =============================================================
#  CLEAN RECORDS
# =============================================================
def clean_records(records):
    """Clean OData records for PostgreSQL."""
    cleaned = []
    for r in records:
        row = {}
        for key, val in r.items():
            if key.startswith("__"):
                continue
            col = re.sub(r'[^a-z0-9_]', '_', key.strip().lower().replace("/", "_"))
            if not col or isinstance(val, (dict, list)):
                continue
            row[col] = str(val).strip() if val is not None else ""
        if row:
            cleaned.append(row)
    return cleaned


# =============================================================
#  SAVE TO POSTGRESQL
# =============================================================
def save_to_postgres(table_name, records):
    """Create table and insert records into whole_sap schema."""
    if not records:
        log.warning(f"    No records to save for {table_name}")
        return 0

    schema = PG["schema"]
    safe_table = re.sub(r'[^a-z0-9_]', '_', table_name.lower())
    if not safe_table:
        return 0

    columns = list(records[0].keys())
    if not columns:
        return 0

    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )

    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
            conn.commit()

            cur.execute(f'DROP TABLE IF EXISTS {schema}."{safe_table}" CASCADE;')
            conn.commit()

            col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
            cur.execute(f"""
                CREATE TABLE {schema}."{safe_table}" (
                    {col_defs},
                    _synced_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
            log.info(f"    Table {schema}.{safe_table} created ({len(columns)} columns)")

            col_str = ", ".join(f'"{c}"' for c in columns)
            val_str = ", ".join(f"%({c})s" for c in columns)
            sql = f'INSERT INTO {schema}."{safe_table}" ({col_str}) VALUES ({val_str});'

            total = 0
            for i in range(0, len(records), PG_BATCH_SIZE):
                batch = records[i:i + PG_BATCH_SIZE]
                try:
                    psycopg2.extras.execute_batch(cur, sql, batch)
                    conn.commit()
                    total += len(batch)
                except Exception as e:
                    conn.rollback()
                    log.error(f"    Batch error: {e}")
                    for rec in batch:
                        try:
                            cur.execute(sql, rec)
                            conn.commit()
                            total += 1
                        except Exception:
                            conn.rollback()

            log.info(f"    ✅ Saved {total}/{len(records)} rows to {schema}.{safe_table}")
            return total
    finally:
        conn.close()


# =============================================================
#  MAIN
# =============================================================
def main():
    # Get services from command line args OR from the SELECTED_SERVICES list
    args = sys.argv[1:]

    if args and args[0] not in ("-h", "--help"):
        selected = [s for s in args]
    else:
        selected = list(SELECTED_SERVICES)

    if not selected or "--help" in args or "-h" in args:
        print("""
Usage: python pull_selected.py [SERVICE1] [SERVICE2] [SERVICE3] ...

You can use EXACT names or KEYWORDS. The script will smart-match!

Examples:
  python pull_selected.py                              # Uses SELECTED_SERVICES list in the file
  python pull_selected.py ZAPI_SALES_ORDER_SRV         # Exact SAP name
  python pull_selected.py SALES_ORDER PRODUCT MATERIAL # Keywords - finds matching services
  python pull_selected.py ZMDG_BP_SRV ZMDG_MATERIAL_SRV ZMD_C_PRODUCT_MAINTAIN_SRV  # 3 services

To see ALL available services:
  python discover_services.py --save

To change default services, edit SELECTED_SERVICES list in this file.
        """)
        return

    start_time = datetime.now()
    log.info("=" * 70)
    log.info("  SELECTED SAP OData Pull")
    log.info(f"  Server   : {SAP['host']}:{SAP['port']}")
    log.info(f"  Schema   : {PG['schema']}")
    log.info(f"  Services : {len(selected)}")
    for s in selected:
        log.info(f"    → {s}")
    log.info(f"  Started  : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 70)

    # Step 1: Discover all services from catalog
    log.info("\n[STEP 1] Discovering services from SAP catalog...")
    all_services = discover_services()

    if not all_services:
        log.error("No services found! Check SAP OData activation.")
        return

    # Step 2: Smart match selected services
    matched, not_found = match_services(selected, all_services)

    if not_found:
        log.warning(f"\n⚠️  Could not find these services: {not_found}")
        log.info("  Tip: Use 'python discover_services.py --save' to see all available names")
        # Show suggestions
        for nf in not_found:
            keywords = [k for k in nf.upper().split("_") if len(k) > 2]
            suggestions = [s["technical_name"] for s in all_services
                          if any(kw in s["technical_name"].upper() for kw in keywords)][:5]
            if suggestions:
                log.info(f"  Similar to '{nf}': {suggestions}")

    if not matched:
        log.error("No services matched! Nothing to pull.")
        return

    log.info(f"\n[STEP 2] Matched {len(matched)} services:")
    for svc in matched:
        log.info(f"  ✓ {svc['technical_name']}")

    # Step 3: Discover entities for matched services
    log.info(f"\n[STEP 3] Discovering entity sets...")
    session  = create_session()
    base_url = get_base_url()

    # Create schema
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG['schema']};")
        conn.commit()
    conn.close()

    total_tables = 0
    total_rows = 0

    for svc in matched:
        svc_name = svc["technical_name"]
        svc_url  = svc["service_url"]

        log.info(f"\n{'━'*60}")
        log.info(f"  SERVICE: {svc_name}")
        log.info(f"{'━'*60}")

        # Get entity sets
        entities = discover_entity_sets(svc_url)
        log.info(f"  Found {len(entities)} entity sets")

        if not entities:
            continue

        # Step 4: Pull data from each entity
        for entity_name in entities:
            log.info(f"\n  📥 [{entity_name}] Pulling...")

            try:
                records = pull_entity_data(session, base_url, svc_url, entity_name)

                if records:
                    cleaned = clean_records(records)
                    if cleaned:
                        table_name = f"{svc_name}_{entity_name}".lower()
                        rows = save_to_postgres(table_name, cleaned)
                        total_rows += rows
                        total_tables += 1
                    else:
                        log.info(f"    No clean data")
                else:
                    log.info(f"    Empty - 0 records")

            except Exception as e:
                log.error(f"    ❌ FAILED: {e}")

    # Summary
    end_time = datetime.now()
    duration = end_time - start_time

    log.info("\n" + "=" * 70)
    log.info("  ✅ PULL COMPLETE")
    log.info("=" * 70)
    log.info(f"  Duration      : {duration}")
    log.info(f"  Services      : {len(matched)}")
    log.info(f"  Tables created: {total_tables}")
    log.info(f"  Total rows    : {total_rows}")
    log.info(f"  Schema        : {PG['schema']}")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
