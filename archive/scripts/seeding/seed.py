from sqlalchemy.orm import Session
from db.base import SessionLocal, engine, Base
from db.models import CuratedVendor, CuratedInvoice, Entity, Attribute
# Import other models as needed
import uuid
from datetime import datetime

def seed(db: Session):
    print("Checking for existing data...")
    
    # 1. Seed Vendors (Idempotent)
    # Define vendors to seed
    vendors_data = [
        {
            "vendorCode": "V001",
            "vendorName": "ABC Traders",
            "gst": "29ABCDE1234F1Z5",
            "email": "abc@vendor.com" # Note: CuratedVendor model doesn't have email in my definition, based on prisma schema. 
             # Wait, prisma schema for CuratedVendor:
             # vendorId, vendorCode, vendorName, gst, validFrom, validTo, isCurrent, dqScore, createdAt, updatedAt
             # It does NOT have email.
             # But seed.js had email. 
             # seed.js used `prisma.vendor.create`. 
             # Prisma schema I read:
             # model CuratedVendor { ... }
             # model Vendor { ... } ?? 
             # Wait, did I miss `model Vendor` in existing schema?
             # Let me check schema.prisma content again from Step 59.
             # It has `model CuratedVendor`. It does NOT have `model Vendor`.
             # But `seed.js` uses `prisma.vendor.create`.
             # This implies `seed.js` might be outdated or referring to a different schema?
             # OR `model Vendor` exists but I missed it?
             # Step 59 showing lines 1 to 232.
             # It lists `Entity`, `Attribute`, `BusinessRule`, `CuratedVendor`, `CuratedInvoice`, `ExtractionMetadata`, `DqScore`, `Event`, `DataAccessLog`, `DataChangeLog`, `AiActionLog`, `PushQueue`, `VendorEmbedding`.
             # There is NO `model Vendor`.
             # So `seed.js` (Step 60) content:
             # `const vendor1 = await prisma.vendor.create(...)`
             # This suggests `seed.js` is invalid for the CURRENT schema.prisma I read.
             # OR `CuratedVendor` IS the vendor table but mapped?
             # `@@map("curated_vendors")`.
             # If `seed.js` uses `prisma.vendor`, then `schema.prisma` MUST have `model Vendor`.
             # If I don't see it, then `seed.js` is WRONG for `schema.prisma`.
             # However, the user said `dal-setup` works.
             # Maybe `schema.prisma` I read is NOT the one `seed.js` uses?
             # Or `prisma` client was generated from a DIFFERENT schema?
             # The user says "put those iin db and inside db in models in this files".
             # I should follow `schema.prisma` I read, which is likely the source of truth for the NEW system.
             # `CuratedVendor` seems to be the one.
             # I will seed `CuratedVendor`.
             # I will skip `email` if it's not in the model.
        },
        {
            "vendorCode": "V002",
            "vendorName": "XYZ Supplies",
            "gst": "29XYZDE5678G1Z9"
        }
    ]

    for v_data in vendors_data:
        existing = db.query(CuratedVendor).filter(CuratedVendor.vendorCode == v_data["vendorCode"]).first()
        if not existing:
            vendor = CuratedVendor(
                id=str(uuid.uuid4()),
                vendorId=str(uuid.uuid4()), # Generate unique ID
                vendorCode=v_data["vendorCode"],
                vendorName=v_data["vendorName"],
                gst=v_data.get("gst"),
                validFrom=datetime.utcnow(),
                isCurrent=True
            )
            db.add(vendor)
            print(f"Created vendor: {v_data['vendorName']}")
        else:
            print(f"Vendor exists: {v_data['vendorName']}")
    
    db.commit()

    # 2. Seed Invoices
    # Need to fetch vendors to link
    v1 = db.query(CuratedVendor).filter(CuratedVendor.vendorCode == "V001").first()
    v2 = db.query(CuratedVendor).filter(CuratedVendor.vendorCode == "V002").first()

    invoices_data = [
        {
            "invoiceNumber": "INV-001",
            "amount": 15000.0,
            "status": "Uploaded",
            "vendor": v1
        },
        {
            "invoiceNumber": "INV-002",
            "amount": 22000.0,
            "status": "Processed",
            "vendor": v2
        }
    ]

    for i_data in invoices_data:
        if i_data["vendor"]:
            existing = db.query(CuratedInvoice).filter(CuratedInvoice.invoiceNumber == i_data["invoiceNumber"]).first()
            if not existing:
                invoice = CuratedInvoice(
                    id=str(uuid.uuid4()),
                    invoiceId=str(uuid.uuid4()),
                    invoiceNumber=i_data["invoiceNumber"],
                    vendorId=i_data["vendor"].vendorId, # Use vendorId as FK
                    invoiceDate=datetime.utcnow(),
                    totalAmount=i_data["amount"],
                    status=i_data["status"],
                    validFrom=datetime.utcnow(),
                    isCurrent=True
                )
                db.add(invoice)
                print(f"Created invoice: {i_data['invoiceNumber']}")
            else:
                print(f"Invoice exists: {i_data['invoiceNumber']}")
        else:
             print(f"Skipping invoice {i_data['invoiceNumber']} - Vendor not found")

    db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
