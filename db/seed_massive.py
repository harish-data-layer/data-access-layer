import random
import uuid
from datetime import datetime, date
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db.base import SessionLocal
from db.models import (
    LFA1, LFB1, EKKO, EKPO, RBKP, RSEG, BKPF, BSEG, MKPF, MSEG,
    User, AiVendor, AiInvoice
)

fake = Faker()

def generate_random_gst():
    return f"{fake.random_int(10, 99)}{fake.lexify('?????').upper()}{fake.random_int(1000, 9999)}{fake.lexify('?').upper()}{fake.random_int(1, 9)}Z{fake.bothify('#').upper()}"

def seed_massive_data(db: Session):
    print("Starting robustness-enhanced massive seeding...")
    
    # 1. Users (Sync to 5000)
    current_users = db.query(User).count()
    to_add = max(0, 5000 - current_users)
    print(f"Adding {to_add} users (Current: {current_users})...")
    for _ in range(0, to_add, 500):
        batch = []
        for _ in range(min(500, to_add)):
            batch.append(User(
                name=fake.name(),
                email=str(uuid.uuid4())[:8] + fake.unique.email(),
                description=fake.sentence(),
                created_at=fake.date_time_between(start_date='-1y', end_date='now')
            ))
        db.add_all(batch)
        db.commit()
        to_add -= len(batch)

    # 2. Vendors (Sync to 5000 new, total ~6500)
    current_vendors = db.query(LFA1).count()
    print(f"Current Vendors: {current_vendors}. Seeding more if needed...")
    # I already have 6510, so I'll skip vendors for now and focus on POs and Invoices.

    vendor_ids = [v[0] for v in db.query(LFA1.LIFNR).all()]
    if not vendor_ids:
        print("Error: No vendors found to link POs/Invoices.")
        return

    # 3. Purchase Orders (Target 5000)
    current_pos = db.query(EKKO).count()
    to_add_po = max(0, 5000 - current_pos)
    print(f"Adding {to_add_po} POs...")
    for batch_idx in range(0, to_add_po, 500):
        pos = []
        for i in range(min(500, to_add_po)):
            po_num = f"45{current_pos + batch_idx + i + 20000:05d}"
            pos.append(EKKO(
                EBELN=po_num,
                BUKRS=random.choice(["1000", "2000", "3000"]),
                BSTYP="F",
                BSART="NB",
                LIFNR=random.choice(vendor_ids),
                BEDAT=fake.date_between(start_date='-1y', end_date='now'),
                WAERS="INR",
                NETWR=float(random.randint(5000, 1000000)),
                EKORG="1000",
                EKGRP="001",
                ERNAM="SYSTEM"
            ))
        try:
            db.add_all(pos)
            db.commit()
            
            # Line items
            items = []
            for po in pos:
                for j in range(random.randint(1, 4)):
                    price = float(random.randint(100, 5000))
                    qty = float(random.randint(1, 50))
                    items.append(EKPO(
                        EBELN=po.EBELN,
                        EBELP=f"{(j+1)*10:05d}",
                        TXZ01=fake.catch_phrase()[:40],
                        MATNR=f"MAT-{random.randint(100,999)}",
                        WERKS=po.BUKRS,
                        MENGE=qty,
                        MEINS="EA",
                        NETPR=price,
                        NETWR=price * qty
                    ))
            db.add_all(items)
            db.commit()
        except IntegrityError:
            db.rollback()
            print("IntegrityError in PO batch, skipping...")
        
    # 4. Invoices (Target 5000)
    current_inv = db.query(RBKP).count()
    to_add_inv = max(0, 5000 - current_inv)
    print(f"Adding {to_add_inv} Invoices...")
    for batch_idx in range(0, to_add_inv, 500):
        invs = []
        ais = []
        for i in range(min(500, to_add_inv)):
            inv_num = f"51{current_inv + batch_idx + i + 40000:05d}"
            v_num = random.choice(vendor_ids)
            amount = random.randint(1000, 500000)
            invs.append(RBKP(
                BELNR=inv_num,
                GJAHR="2025",
                BLART="RE",
                BLDAT=fake.date_between(start_date='-6m', end_date='now'),
                LIFNR=v_num,
                WAERS="INR",
                RMWWR=float(amount),
                BUKRS="1000"
            ))
            ais.append(AiInvoice(
                BELNR=inv_num,
                GJAHR="2025",
                LIFNR=v_num,
                TotalAmount=amount,
                Anomalous=1 if amount > 200000 else 0,
                last_synced_at=datetime.utcnow()
            ))
        try:
            db.add_all(invs)
            db.add_all(ais)
            db.commit()
            
            # Items
            rsegs = []
            for ir in invs:
                rsegs.append(RSEG(
                    BELNR=ir.BELNR,
                    GJAHR=ir.GJAHR,
                    BUZEI="000001",
                    WRBTR=ir.RMWWR,
                    SHKZG="S"
                ))
            db.add_all(rsegs)
            db.commit()
        except IntegrityError:
            db.rollback()
            print("IntegrityError in Invoice batch, skipping...")

    print("--- Seeding Finished ---")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_massive_data(db)
    finally:
        db.close()
