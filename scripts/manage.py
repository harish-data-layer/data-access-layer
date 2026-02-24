import sys
import os
import random
from sqlalchemy import text
from datetime import date, datetime

# --- PEP 8 STANDARDS: PATH SETUP ---
# Ensures Python can find the 'db' and 'services' folders
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import SessionLocal, engine, Base
from db.models.sap_tables import LFA1, RBKP, EKKO, EKPO
from db.models.test import AiVendor, AiInvoice
from db.services.ai_sync_service import SyncService

class MasterController:
    """
    The Single Source of Truth for database management.
    One class to handle everything from setup to seeding.
    """

    def __init__(self):
        self.db = SessionLocal()

    def setup(self, count=100):
        """
        THE MASTER COMMAND: Setup database, tables, seed data, and sync AI scores.
        Usage: python manage.py setup
        """
        print("\n--- [STEP 1] Initializing Cloud Database ---")
        try:
            # Connect and ensure schemas exist
            with engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS sap;"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai;"))
                conn.commit()
            
            # Create all tables defined in our models if they don't exist
            print("[STEP 2] Creating Tables...")
            Base.metadata.create_all(bind=engine)
            
            # Step 3 (Wipe) removed as per user request to preserve data

            print(f"[STEP 3] Adding {count} Fresh Records (if not already present)...")
            vendor_names = ["Reliance", "Tata", "Infosys", "Wipro", "HCL", "Mahindra", "Adani"]
            
            # Start ID based on current time to avoid collisions with previous runs
            ts_id = int(datetime.now().timestamp()) % 10000 
            
            for i in range(count):
                lifnr = f"V{ts_id + i}"
                name = f"{random.choice(vendor_names)} {ts_id + i}"
                
                # Check if vendor exists
                exists = self.db.query(LFA1).filter(LFA1.LIFNR == lifnr).first()
                if not exists:
                    # Add Local Vendor Record (SAP Layer)
                    self.db.add(LFA1(LIFNR=lifnr, NAME1=name, COUNTRY="IN", ERDAT=date.today()))
                    
                    # Add Local Invoice Record (SAP Layer)
                    belnr = f"51{ts_id + i}"
                    self.db.add(RBKP(BELNR=belnr, GJAHR="2025", LIFNR=lifnr, RMWWR=5000.0, BUKRS="1000"))
                
                if i % 50 == 0:
                    self.db.commit()
            
            self.db.commit()
            print(f"--- Success: New records added to SAP schema ---")

            # Final Step: Sync to AI layer
            print("[STEP 4] Running AI Scoring Logic for all records...")
            results = SyncService.sync_sap_to_ai(self.db)
            print(f"--- Success: AI Layer updated (Stats: {results}) ---")
            
            print("\n[FINISH] Your production environment is READY.")

        except Exception as e:
            print(f"Error during setup: {e}")
            self.db.rollback()

    def close(self):
        self.db.close()

if __name__ == "__main__":
    controller = MasterController()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "setup":
            # The only command the user needs
            controller.setup()
        else:
            print("Usage: python manage.py setup")
    finally:
        controller.close()
