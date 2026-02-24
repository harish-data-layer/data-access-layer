# Import Session for type hinting database connections
from sqlalchemy.orm import Session
# Import SessionLocal to create new database sessions if needed
from db.base import SessionLocal
# Import SAP and AI models to interact with the database tables
from db.models import LFA1, RBKP, AiVendor, AiInvoice
# Import datetime to timestamp synchronization events
from datetime import datetime

# Define the SyncService class to handle data movement between schemas
class SyncService:
    """
    Service class responsible for the 'Pull and Push' logic between 
    the SAP (source) schema and the AI (target) schema.
    """

    @staticmethod
    def sync_sap_to_ai(db: Session, limit: int = 100):
        """
        Synchronizes Vendor and Invoice data from SAP tables to AI tables.
        
        Args:
            db (Session): The active database session to use.
            limit (int): The maximum number of records to process in one batch.
            
        Returns:
            dict: A summary of how many records were newly synced.
        """
        # Initialize a dictionary to track synchronization statistics
        stats = {"vendors_synced": 0, "invoices_synced": 0}

        # --- STEP 1: VENDOR SYNCHRONIZATION ---
        # Query the raw SAP Vendor table (LFA1) with the specified limit
        sap_vendors = db.query(LFA1).limit(limit).all()
        
        # Iterate through each vendor retrieved from SAP
        for v in sap_vendors:
            # Check if this specific vendor already exists in the AI layer
            ai_v = db.query(AiVendor).filter(AiVendor.LIFNR == v.LIFNR).first()
            
            # If the vendor is missing from the AI layer, create a new record
            if not ai_v:
                db.add(AiVendor(
                    LIFNR=v.LIFNR,
                    NAME1=v.NAME1,
                    AI_Score=85,  # Default safety score for new vendors
                    AI_Classification="Automated Sync",
                    last_synced_at=datetime.utcnow()
                ))
                # Increment the vendor sync counter
                stats["vendors_synced"] += 1
            else:
                # If it exists, update the name and the sync timestamp
                ai_v.NAME1 = v.NAME1
                ai_v.last_synced_at = datetime.utcnow()

        # --- STEP 2: INVOICE SYNCHRONIZATION ---
        # Query the raw SAP Invoice header table (RBKP)
        sap_invoices = db.query(RBKP).limit(limit).all()
        
        # Iterate through each invoice retrieved from SAP
        for inv in sap_invoices:
            # Check for existing record using Composite Key (Invoice Number + Fiscal Year)
            ai_inv = db.query(AiInvoice).filter(
                AiInvoice.BELNR == inv.BELNR, 
                AiInvoice.GJAHR == inv.GJAHR
            ).first()
            
            # If the invoice hasn't been synced yet, process it
            if not ai_inv:
                # Basic Anomaly Detection: Flag invoices over 100,000 for review
                is_anomalous = 1 if (inv.RMWWR or 0) > 100000 else 0
                
                # Add the new invoice to the AI schema
                db.add(AiInvoice(
                    BELNR=inv.BELNR,
                    GJAHR=inv.GJAHR,
                    LIFNR=inv.LIFNR,
                    TotalAmount=int(inv.RMWWR or 0),
                    Anomalous=is_anomalous,
                    last_synced_at=datetime.utcnow()
                ))
                # Increment the invoice sync counter
                stats["invoices_synced"] += 1

        # Commit all changes to the database to finalize the synchronization
        db.commit()
        
        # Return the final stats to the caller
        return stats

# Entry point for running the sync service as a standalone script
if __name__ == "__main__":
    # Create a local database session
    db = SessionLocal()
    try:
        print("Starting Data Synchronization...")
        # Execute the sync logic
        results = SyncService.sync_sap_to_ai(db)
        # Output the results to the console
        print(f"Synchronization Complete: {results}")
    finally:
        # Ensure the database session is closed even if an error occurs
        db.close()
