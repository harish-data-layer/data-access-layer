import random
import os
import sys
from datetime import date, timedelta

# Add the project root to the path so it can find the 'db' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.base import SessionLocal, engine, Base
from db.models.sap_tables import LFA1, LFB1, EKKO, EKPO, RBKP, RSEG, BKPF, BSEG, MKPF, MSEG

# ==========================================================
# 🟢 MANAGE YOUR DATA HERE (Hardcoded Real-looking Data)
# ==========================================================

# You can add as many real vendors as you want here
RAW_VENDORS = [
    {"LIFNR": "V20001", "NAME1": "Amazon Business Services", "COUNTRY": "US"},
    {"LIFNR": "V20002", "NAME1": "Microsoft Cloud Solutions", "COUNTRY": "US"},
    {"LIFNR": "V20003", "NAME1": "Siemens Industrial", "COUNTRY": "DE"},
    {"LIFNR": "V20004", "NAME1": "Reliance Industries", "COUNTRY": "IN"},
    {"LIFNR": "V20005", "NAME1": "Tata Consultancy Services", "COUNTRY": "IN"},
    {"LIFNR": "V20006", "NAME1": "SAP Global Support", "COUNTRY": "DE"},
    {"LIFNR": "V20007", "NAME1": "Infosys Technologies", "COUNTRY": "IN"},
    {"LIFNR": "V20008", "NAME1": "Toyota Motors Corp", "COUNTRY": "JP"},
    {"LIFNR": "V20009", "NAME1": "Samsung Electronics", "COUNTRY": "KR"},
    {"LIFNR": "V20010", "NAME1": "Apple Supply Chain", "COUNTRY": "US"},
]

# You can define specific materials or other data points below
COMPANY_CODES = ["1000", "2000", "3000"]
CURRENCIES = ["USD", "EUR", "INR", "GBP", "JPY"]

# ==========================================================
# 🛠️ SEEDING LOGIC (Don't touch unless adding new tables)
# ==========================================================

def get_random_date():
    return date(2024, 1, 1) + timedelta(days=random.randint(0, 365))

def seed_sap_data(target_count=500):
    db = SessionLocal()
    print(f"\n--- Starting Data Seeding (Target: {target_count} records) ---")
    
    try:
        # Step 0: Clean Tables
        print("Clearing existing data...")
        with engine.connect() as conn:
            tables = ["rseg", "rbkp", "mseg", "mkpf", "bseg", "bkpf", "ekpo", "ekko", "lfb1", "lfa1"]
            for t in tables:
                conn.execute(text(f"TRUNCATE TABLE sap.{t} CASCADE;"))
            conn.commit()

        # Step 1: Seed Vendors (LFA1)
        print("Inserting Hardcoded Vendors...")
        vendor_ids = []
        
        # First, add the hardcoded ones from the list above
        for entry in RAW_VENDORS:
            v = LFA1(
                LIFNR=entry["LIFNR"],
                NAME1=entry["NAME1"],
                COUNTRY=entry["COUNTRY"],
                ERDAT=date.today()
            )
            db.add(v)
            vendor_ids.append(entry["LIFNR"])
        
        # Then, fill up the remaining to reach target_count with synthetic data
        remaining = max(0, target_count - len(RAW_VENDORS))
        if remaining > 0:
            print(f"Generating {remaining} additional synthetic vendors...")
            for i in range(remaining):
                lifnr = f"V{30000 + i}"
                db.add(LFA1(
                    LIFNR=lifnr,
                    NAME1=f"Synthetic Vendor {i}",
                    COUNTRY=random.choice(["US", "DE", "IN", "UK", "JP"]),
                    ERDAT=get_random_date()
                ))
                vendor_ids.append(lifnr)
        db.commit()

        # Step 2: Seed Other Tables (Linking to Vendor IDs)
        print(f"Propagating data to other {len(vendor_ids)} records per table...")
        
        for vid in vendor_ids:
            # LFB1 (Company Code)
            db.add(LFB1(LIFNR=vid, BUKRS=random.choice(COMPANY_CODES), ERDAT=get_random_date()))
            
            # EKKO / EKPO (Purchasing)
            ebeln = f"45{vid[1:]}"
            db.add(EKKO(EBELN=ebeln, BUKRS=random.choice(COMPANY_CODES), AEDAT=get_random_date(), 
                        LIFNR=vid, WAERS=random.choice(CURRENCIES), NETWR=random.uniform(500, 50000)))
            db.add(EKPO(EBELN=ebeln, EBELP="00010", MATNR=f"MAT-{random.randint(100, 999)}", 
                        MENGE=random.uniform(1, 100), NETPR=random.uniform(10, 500), NETWR=random.uniform(100, 5000)))
            
            # RBKP / RSEG (Invoice)
            belnr = f"51{vid[1:]}"
            db.add(RBKP(BELNR=belnr, GJAHR="2024", BLDAT=get_random_date(), BUDAT=get_random_date(), 
                        LIFNR=vid, BUKRS=random.choice(COMPANY_CODES), RMWWR=random.uniform(500, 20000)))
            db.add(RSEG(BELNR=belnr, GJAHR="2024", BUZEI="000001", EBELN=ebeln, 
                        WRBTR=random.uniform(500, 20000), MENGE=random.uniform(1, 100)))

            # BKPF / BSEG (Accounting)
            acc_belnr = f"10{vid[1:]}"
            db.add(BKPF(BUKRS=random.choice(COMPANY_CODES), BELNR=acc_belnr, GJAHR="2024", 
                        BLDAT=get_random_date(), BUDAT=get_random_date(), WAERS=random.choice(CURRENCIES)))
            db.add(BSEG(BUKRS=random.choice(COMPANY_CODES), BELNR=acc_belnr, GJAHR="2024", 
                        BUZEI="001", DMBTR=random.uniform(100, 10000), WRBTR=random.uniform(100, 10000), LIFNR=vid))

            # MKPF / MSEG (Material Document)
            mat_belnr = f"50{vid[1:]}"
            db.add(MKPF(MBLNR=mat_belnr, MJAHR="2024", BLDAT=get_random_date(), 
                        BUDAT=get_random_date(), USNAM="ADMIN"))
            db.add(MSEG(MBLNR=mat_belnr, MJAHR="2024", ZEILE="0001", BWART="101", 
                        MATNR=f"MAT-{random.randint(100, 999)}", MENGE=random.uniform(1, 50), LIFNR=vid))

        db.commit()
        print(f"\n--- Success: Database fully synced with {len(vendor_ids)} records per table ---")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Change this number to seed more or less
    seed_sap_data(500)
