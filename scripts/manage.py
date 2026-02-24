import sys
import os
import random
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import SessionLocal
from db.models.sap_tables import RBKP, RSEG, BKPF, BSEG, LFA1, LFB1, EKKO, EKPO, MKPF, MSEG
from db.models.test import (
    AiVendor, AiInvoice, SyncState, PromotedVendor, 
    PromotedInvoice, PromotedInventory, PromotedPurchaseOrder
)
from db.models.audit_log import DataAccessLog, DataChangeLog
from db.services.ai_sync_service import SyncService

class DatabaseManager:
    def __init__(self):
        self.db = SessionLocal()

    def clear_data(self):
        """Wipes all data for a clean slate."""
        print("Clearing all datasets...")
        tables = [
            SyncState, PromotedInventory, PromotedInvoice, PromotedPurchaseOrder, PromotedVendor,
            AiInvoice, AiVendor, MSEG, MKPF, BSEG, BKPF, RSEG, RBKP, EKPO, EKKO, LFB1, LFA1,
            DataAccessLog, DataChangeLog
        ]
        for table in tables:
            try:
                self.db.query(table).delete()
            except:
                self.db.rollback()
        self.db.commit()

    def seed_data(self, count=100):
        """Generates realistic data."""
        self.clear_data()
        print(f"Seeding {count} records...")
        
        vendor_names = ["Reliance", "Tata", "Infosys", "Wipro", "HCL", "Adani", "Mahindra"]
        
        for i in range(count):
            lifnr = f"V{1000+i}"
            name = f"{random.choice(vendor_names)} {i}"
            
            self.db.add(LFA1(LIFNR=lifnr, NAME1=name, COUNTRY="IN", ERDAT=date.today()))
            self.db.add(AiVendor(LIFNR=lifnr, NAME1=name, AI_Score=random.randint(60, 95)))
            
            ebeln = f"45{10000+i}"
            self.db.add(EKKO(EBELN=ebeln, LIFNR=lifnr, BEDAT=date.today(), BUKRS="1000", WAERS="INR"))
            self.db.add(EKPO(EBELN=ebeln, EBELP="10", MATNR="MAT-01", MENGE=10.0, NETWR=5000.0, BUKRS="1000", WERKS="1100"))
            
            belnr = f"51{10000+i}"
            self.db.add(RBKP(BELNR=belnr, GJAHR="2025", LIFNR=lifnr, RMWWR=5900.0, BUKRS="1000", WAERS="INR"))
            
            if i % 100 == 0:
                self.db.commit()
        
        self.db.commit()
        print(f"Success: Seeded {count} records.")

    def run_sync(self):
        """Runs Sync."""
        print("Syncing...")
        stats = SyncService.sync_sap_to_ai(self.db)
        print(f"Result: {stats}")

    def close(self):
        self.db.close()

if __name__ == "__main__":
    manager = DatabaseManager()
    try:
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            if cmd == "seed":
                count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
                manager.seed_data(count)
            elif cmd == "sync":
                manager.run_sync()
            elif cmd == "clear":
                manager.clear_data()
            else:
                print("Usage: python manage.py [seed|sync|clear]")
        else:
            print("Usage: python manage.py [seed|sync|clear]")
    finally:
        manager.close()
