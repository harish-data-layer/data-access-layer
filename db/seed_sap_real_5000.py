"""
Final Comprehensive Dataset Seeder
Seeds SAP, AI, and Audit layers with 500+ records each.
Ensures zero nulls in sync state and populates all transactional tables.
"""
import random
import uuid as uuid_pkg
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from db.base import SessionLocal
from db.models.sap_tables import RBKP, RSEG, BKPF, BSEG, LFA1, LFB1, EKKO, EKPO, MKPF, MSEG
from db.models.test import (
    User, AiVendor, AiInvoice, SyncState, PromotedVendor, 
    PromotedInvoice, PromotedInventory, PromotedPurchaseOrder
)
from db.models.audit_log import DataAccessLog, DataChangeLog

# --- CONFIGURATION ---
TARGET_COUNT = 500
VENDOR_TARGET_COUNT = 500 
BATCH_SIZE = 50 # Smaller batch due to many tables

# Base list of real vendors
REAL_VENDORS_BASE = [
    ("Reliance Industries Ltd", "27AAACR4849R1Z9", "Mumbai", "400001"),
    ("Tata Consultancy Services", "27AABCT1332L1ZV", "Mumbai", "400001"),
    ("HDFC Bank Limited", "27AAACH2702H1Z7", "Mumbai", "400001"),
    ("Infosys Limited", "29AABCI1681G1ZK", "Bengaluru", "560100"),
    ("ICICI Bank Limited", "24AABCI1681G1Z1", "Vadodara", "390007"),
    ("SAP India Pvt Ltd", "29AABCS4259H1ZU", "Bengaluru", "560066"),
    ("Oracle India Pvt Ltd", "29AABCO0538N1ZX", "Bengaluru", "560076"),
    ("Microsoft India", "29AABCM4011G1ZR", "Hyderabad", "500032"),
]

def generate_gst(idx):
    return f"{random.randint(10,35)}ABCDE{1000+idx:04d}F1Z{random.randint(1,9)}"

def get_expanded_vendors():
    vendors = []
    for i, (name, gst, city, post) in enumerate(REAL_VENDORS_BASE):
        vendors.append((f"V{1000+i}", name, "IN", gst, "KRED", city, post))
    
    prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Zenith", "Apex"]
    segments = ["Trading", "Logistics", "Services", "Digital", "Consulting", "Global"]
    suffixes = ["Corp", "Limited", "Sons", "Group", "Agency"]
    cities = [("Chennai", "600001"), ("Pune", "411001"), ("Kolkata", "700001"), ("Ahmedabad", "380001")]

    for i in range(len(REAL_VENDORS_BASE), VENDOR_TARGET_COUNT):
        name = f"{random.choice(prefixes)} {random.choice(segments)} {random.choice(suffixes)} {i}"
        city, post = random.choice(cities)
        vendors.append((f"V{1000+i}", name[:35], "IN", generate_gst(i), "KRED", city, post))
    return vendors

REAL_VENDORS = get_expanded_vendors()

REAL_MATERIALS = [
    ("MAT-I-101", "Industrial Steel", "KG", 450),
    ("MAT-C-202", "Circuit Board", "EA", 2500),
    ("MAT-W-303", "Wireless Router", "EA", 5500),
]

def clear_data(db: Session):
    print("Clearing all layers for a clean seed...")
    tables = [
        SyncState, PromotedInventory, PromotedInvoice, PromotedPurchaseOrder, PromotedVendor,
        AiInvoice, AiVendor, MSEG, MKPF, BSEG, BKPF, RSEG, RBKP, EKPO, EKKO, LFB1, LFA1,
        DataAccessLog, DataChangeLog
    ]
    for table in tables:
        try:
            db.query(table).delete()
            db.commit()
        except Exception as e:
            print(f"Warning: Could not clear {table.__tablename__}: {e}")
            db.rollback()

def update_sync_state(db: Session, entity: str, count: int):
    state = db.query(SyncState).filter(SyncState.entity_name == entity).first()
    if not state:
        state = SyncState(
            entity_name=entity,
            last_sync_at=datetime.now(timezone.utc),
            last_watermark=f"SEQ-{random.randint(1000,9999)}",
            records_synced=count,
            last_status="SUCCESS",
            last_error="NONE",
            total_syncs=1
        )
        db.add(state)
    else:
        state.records_synced = count
        state.total_syncs += 1
        state.last_status = "SUCCESS"
        state.last_sync_at = datetime.now(timezone.utc)
    db.commit()

def seed(db: Session):
    clear_data(db)
    
    # 1. Vendors (Master Data)
    print(f"Seeding {len(REAL_VENDORS)} Vendors & Master relations...")
    for i, (lifnr, name, land, stcd, ktokk, city, post) in enumerate(REAL_VENDORS):
        # LFA1
        db.add(LFA1(
            LIFNR=lifnr, NAME1=name, COUNTRY=land, STCD1=stcd, KTOKK=ktokk, 
            CITY1=city, POST_CODE1=post, ERDAT=date.today(), ERNAM="ADMIN",
            LANGU="EN", BRSCH="SERV", SMTP_ADDR=f"contact@{lifnr.lower()}.com"
        ))
        # LFB1
        db.add(LFB1(LIFNR=lifnr, BUKRS="1000", AKONT="160000", ZTERM="N030", ERDAT=date.today(), ERNAM="ADMIN"))
        # AiVendor
        db.add(AiVendor(LIFNR=lifnr, NAME1=name, AI_Score=random.randint(70,98), AI_Classification="Verified"))
        # PromotedVendor
        db.add(PromotedVendor(vendor_id=5000+i, sap_code=lifnr, name=name, tax_id=stcd, city=city, country_code=land, created_by="AI_VERIFIER"))
        
        if i % 100 == 0:
            db.commit()
    db.commit()

    # 2. Transactions (Documents)
    print(f"Generating {TARGET_COUNT} full document cycles (PO -> GR -> IR -> FI)...")
    for idx in range(TARGET_COUNT):
        ebeln = f"45{10000+idx}" # Purchase Order
        mblnr = f"50{10000+idx}" # Material Doc
        belnr_inv = f"51{10000+idx}" # Invoice Doc
        belnr_acc = f"10{10000+idx}" # Accounting Doc
        
        v_idx = idx % len(REAL_VENDORS)
        lifnr = REAL_VENDORS[v_idx][0]
        mat = random.choice(REAL_MATERIALS)
        qty = random.randint(10, 100)
        net_val = qty * mat[3]
        tax_val = net_val * 0.18
        gross_val = net_val + tax_val
        doc_date = date.today() - timedelta(days=random.randint(1, 30))

        # --- PURCHAING (EKKO/EKPO) ---
        db.add(EKKO(EBELN=ebeln, BUKRS="1000", LIFNR=lifnr, BEDAT=doc_date, WAERS="INR", NETWR=float(net_val), EKORG="1000", EKGRP="001", ERNAM="ADMIN"))
        db.add(EKPO(EBELN=ebeln, EBELP="10", MATNR=mat[0], TXZ01=mat[1], MENGE=float(qty), MEINS=mat[2], NETPR=float(mat[3]), NETWR=float(net_val), BUKRS="1000", WERKS="1100"))

        # --- GOODS RECEIPT (MKPF/MSEG) ---
        db.add(MKPF(MBLNR=mblnr, MJAHR="2025", VGART="WE", BLART="WE", BLDAT=doc_date, BUDAT=doc_date, USNAM="ADMIN", TCODE="MIGO", XBLNR="GR-REF"))
        db.add(MSEG(MBLNR=mblnr, MJAHR="2025", ZEILE="0001", BWART="101", MATNR=mat[0], WERKS="1100", LGORT="0001", LIFNR=lifnr, MENGE=float(qty), MEINS=mat[2], EBELN=ebeln, EBELP="10"))

        # --- INVOICE RECEIPT (RBKP/RSEG) ---
        db.add(RBKP(BELNR=belnr_inv, GJAHR="2025", BLART="RE", BLDAT=doc_date, BUDAT=doc_date, USNAM="ADMIN", LIFNR=lifnr, WAERS="INR", BUKRS="1000", RMWWR=float(gross_val), WMWST=float(tax_val)))
        db.add(RSEG(BELNR=belnr_inv, GJAHR="2025", BUZEI="0001", EBELN=ebeln, EBELP="10", MATNR=mat[0], WERKS="1100", WRBTR=float(net_val), MENGE=float(qty), BUKRS="1000"))

        # --- ACCOUNTING (BKPF/BSEG) ---
        db.add(BKPF(BUKRS="1000", BELNR=belnr_acc, GJAHR="2025", BLART="KR", BLDAT=doc_date, BUDAT=doc_date, USNAM="ADMIN", WAERS="INR", XBLNR="INV-REF"))
        db.add(BSEG(BUKRS="1000", BELNR=belnr_acc, GJAHR="2025", BUZEI="001", BSCHL="31", KOART="K", LIFNR=lifnr, WRBTR=float(gross_val), SHKZG="H"))

        # --- AI & PROMOTED LAYER ---
        db.add(AiInvoice(BELNR=belnr_inv, GJAHR="2025", LIFNR=lifnr, TotalAmount=int(gross_val), Anomalous=0))
        db.add(PromotedPurchaseOrder(po_number=ebeln, item_number=10, vendor_code=lifnr, material_number=mat[0], description=mat[1], quantity=qty, net_price=int(mat[3]), po_date=datetime.now()))
        db.add(PromotedInvoice(invoice_number=belnr_inv, fiscal_year=2025, vendor_code=lifnr, total_amount=int(gross_val), invoice_date=datetime.now(), posting_date=datetime.now()))
        db.add(PromotedInventory(doc_number=mblnr, doc_year=2025, item_number=1, movement_type="101", material_number=mat[0], plant="1100", quantity=qty, unit=mat[2]))

        # --- AUDIT LOGS ---
        db.add(DataAccessLog(entityName="MaterialDocument", recordId=mblnr, operation="POST", accessedBy="ADMIN", accessedByType="USER"))

        if idx % BATCH_SIZE == 0:
            db.commit()
            print(f"  Batch {idx} processed...")

    db.commit()

    # 3. Final Sync States
    entities = ["PromoteVendor", "PromoteInvoice", "PromotePurchaseOrder", "PromoteInventory", "SAP_to_AI_Vendor"]
    for ent in entities:
        update_sync_state(db, ent, TARGET_COUNT if "Vendor" not in ent else VENDOR_TARGET_COUNT)

    print(f"\n[FINISH] Seeded {TARGET_COUNT} documents and {VENDOR_TARGET_COUNT} master records with zero nulls.")

if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()
