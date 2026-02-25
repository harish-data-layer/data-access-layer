from sap_client import SAPClient
from db import PostgresDB
from config import SAP_SERVICES
from logger import get_logger

log = get_logger("MATERIALS")

TABLE_NAME = "MARA"
TABLE_COLUMNS = {
    "product":              "TEXT PRIMARY KEY",
    "product_type":         "TEXT",
    "base_unit":            "TEXT",
    "product_group":        "TEXT",
    "division":             "TEXT",
    "gross_weight":         "NUMERIC",
    "net_weight":           "NUMERIC",
    "weight_unit":          "TEXT",
    "created_on":           "DATE",
    "changed_on":           "DATE",
    "is_marked_for_deletion": "BOOLEAN",
    "synced_at":            "TIMESTAMP DEFAULT NOW()",
}

def map_sap_to_pg(sap_record: dict) -> dict:
    """Maps SAP record (either OData or GUI) to PostgreSQL format."""
    # OData field names vs GUI Technical names
    return {
        "product":                sap_record.get("Product") or sap_record.get("MATNR", ""),
        "product_type":           sap_record.get("ProductType") or sap_record.get("MTART", ""),
        "base_unit":              sap_record.get("BaseUnit") or sap_record.get("MEINS", ""),
        "product_group":          sap_record.get("ProductGroup") or sap_record.get("MATKL", ""),
        "division":               sap_record.get("Division") or sap_record.get("SPART", ""),
        "gross_weight":           float(sap_record.get("GrossWeight") or sap_record.get("BRGEW") or 0),
        "net_weight":             float(sap_record.get("NetWeight") or sap_record.get("NTGEW") or 0),
        "weight_unit":            sap_record.get("WeightUnit") or sap_record.get("GEWEI", ""),
        "created_on":             sap_record.get("CreationDate") or sap_record.get("ERSDA", None),
        "changed_on":             sap_record.get("LastChangeDate") or sap_record.get("LAEDA", None),
        "is_marked_for_deletion": sap_record.get("IsMarkedForDeletion") or (sap_record.get("LVORM") == 'X'),
    }

def map_pg_to_sap(pg_record: dict) -> dict:
    return {
        "Product":      pg_record.get("product", ""),
        "ProductType":  pg_record.get("product_type", ""),
        "BaseUnit":     pg_record.get("base_unit", ""),
        "ProductGroup": pg_record.get("product_group", ""),
        "Division":     pg_record.get("division", ""),
        "GrossWeight":  str(pg_record.get("gross_weight", 0)),
        "NetWeight":    str(pg_record.get("net_weight", 0)),
        "WeightUnit":   pg_record.get("weight_unit", ""),
    }

def pull_sap_to_postgres(product_type: str = None):
    sap = SAPClient()
    db  = PostgresDB()
    try:
        db.create_table_if_not_exists(TABLE_NAME, TABLE_COLUMNS)
        params = {
            "$select": "Product,ProductType,BaseUnit,ProductGroup,Division,"
                       "GrossWeight,NetWeight,WeightUnit,CreationDate,"
                       "LastChangeDate,IsMarkedForDeletion",
            "$orderby": "Product asc",
        }
        if product_type:
            params["$filter"] = f"ProductType eq '{product_type}'"
        
        sap_records = sap.pull(SAP_SERVICES["material"], "A_Product", params)
        if not sap_records:
            return 0
            
        pg_records = [map_sap_to_pg(r) for r in sap_records]
        return db.upsert(TABLE_NAME, pg_records, primary_key="product")
    finally:
        db.close()

def push_postgres_to_sap(product_id: str = None):
    sap = SAPClient()
    db  = PostgresDB()
    try:
        where = f"product = '{product_id}'" if product_id else None
        pg_records = db.read(TABLE_NAME, where=where)
        success: int = 0
        for row in pg_records:
            try:
                sap_payload = map_pg_to_sap(row)
                sap.push_update(SAP_SERVICES["material"], f"A_Product('{row['product']}')", sap_payload)
                success += 1
            except Exception as e:
                log.error(f"Push failed for {row['product']}: {e}")
        return success
    finally:
        db.close()
