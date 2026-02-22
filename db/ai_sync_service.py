from sqlalchemy.orm import Session
from db.base import SessionLocal
from db.models import LFA1, RBKP, AiVendor, AiInvoice
from datetime import datetime

def pull_sap_to_ai(db: Session):
    """
    Demonstrates 'PULLING' data from SAP schema and 'PUSHING' it to AI schema 
    with added intelligence (risk scoring/anomaly detection).
    """
    print("\n--- Starting SAP to AI Synchronization (PULL -> TRANSFORM -> PUSH) ---")

    # 1. Pull Vendors from SAP LFA1
    print("Pulling Vendors from SAP.LFA1...")
    sap_vendors = db.query(LFA1).limit(10).all()
    
    for v in sap_vendors:
        # Check if AI already has this record
        ai_v = db.query(AiVendor).filter(AiVendor.LIFNR == v.LIFNR).first()
        
        if not ai_v:
            # PUSH: Create new AI record with a generated score
            ai_v = AiVendor(
                LIFNR=v.LIFNR,
                NAME1=v.NAME1,
                AI_Score=85, # Example calculated score
                AI_Classification="Automated Sync",
                last_synced_at=datetime.utcnow()
            )
            db.add(ai_v)
            print(f"  [NEW] Synced Vendor {v.LIFNR} to AI layer")
        else:
            # UPDATE: Update existing AI record
            ai_v.NAME1 = v.NAME1
            ai_v.last_synced_at = datetime.utcnow()
            print(f"  [UPD] Refreshed Vendor {v.LIFNR} in AI layer")

    # 2. Pull Invoices from SAP RBKP
    print("\nPulling Invoices from SAP.RBKP...")
    sap_invoices = db.query(RBKP).limit(10).all()

    for inv in sap_invoices:
        ai_inv = db.query(AiInvoice).filter(
            AiInvoice.BELNR == inv.BELNR, 
            AiInvoice.GJAHR == inv.GJAHR
        ).first()

        if not ai_inv:
            # Detect Anomaly logic (Example: amount > 100k)
            is_anomalous = 1 if (inv.RMWWR or 0) > 100000 else 0
            
            ai_inv = AiInvoice(
                BELNR=inv.BELNR,
                GJAHR=inv.GJAHR,
                LIFNR=inv.LIFNR,
                TotalAmount=int(inv.RMWWR or 0),
                Anomalous=is_anomalous,
                last_synced_at=datetime.utcnow()
            )
            db.add(ai_inv)
            print(f"  [NEW] Synced Invoice {inv.BELNR} (Fiscal Year {inv.GJAHR}) to AI layer")
        else:
            print(f"  [SKIP] Invoice {inv.BELNR} already synced")

    db.commit()
    print("\n--- Sync Complete ---")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        pull_sap_to_ai(db)
    finally:
        db.close()
