"""
SAP Comprehensive Sample Data Seeder - 100+ records with full FK mapping
All records are properly linked:
  LFA1 (vendors) → LFB1 (company codes)
  LFA1 → EKKO (POs) → EKPO (PO items)
  LFA1 → RBKP (invoices) → RSEG (invoice lines) → EKPO (PO reference)
  BKPF (accounting headers) → BSEG (accounting lines)
  MKPF (material doc headers) → MSEG (material lines) → EKPO (PO reference)

Run: python -m db.seed_sap_full
"""
from datetime import date, timedelta
from db.base import SessionLocal
from db.models.sap_tables import RBKP, RSEG, BKPF, BSEG, LFA1, LFB1, EKKO, EKPO, MKPF, MSEG

# ─── Master Data ────────────────────────────────────────────────────────────

VENDORS = [
    ("V001", "Tata Consultancy Services Ltd",    "IN", "27AABCT1332L1ZV", "KRED"),
    ("V002", "Infosys Limited",                  "IN", "29AABCI1681G1ZK", "KRED"),
    ("V003", "Wipro Technologies Ltd",           "IN", "29AAACW0867H1ZQ", "KRED"),
    ("V004", "HCL Technologies Ltd",             "IN", "09AAACH1645R1ZE", "KRED"),
    ("V005", "Tech Mahindra Ltd",                "IN", "27AABCT3518Q1ZF", "KRED"),
    ("V006", "SAP India Pvt Ltd",               "IN", "29AABCS4259H1ZU", "KRED"),
    ("V007", "Oracle India Pvt Ltd",            "IN", "29AABCO0538N1ZX", "KRED"),
    ("V008", "Microsoft India Pvt Ltd",         "IN", "29AABCM4011G1ZR", "KRED"),
    ("V009", "IBM India Pvt Ltd",               "IN", "29AABCI0638B1ZD", "KRED"),
    ("V010", "Accenture Solutions Pvt Ltd",     "IN", "29AABCA3678M1ZT", "KRED"),
    ("V011", "Cognizant Technology Solutions",  "IN", "33AABCC4270P1ZN", "KRED"),
    ("V012", "Capgemini India Pvt Ltd",         "IN", "29AABCC7873Q1ZL", "KRED"),
    ("V013", "L&T Infotech Ltd",                "IN", "27AABCL0100N1ZB", "KRED"),
    ("V014", "Mphasis Ltd",                     "IN", "29AABCM2476G1ZV", "KRED"),
    ("V015", "Hexaware Technologies Ltd",       "IN", "27AABCH3096B1ZT", "KRED"),
]

COMPANY_CODES = ["1000", "2000", "3000"]

MATERIALS = [
    ("MAT-IT-001", "Laptop Dell XPS 15",        "EA"),
    ("MAT-IT-002", "Desktop HP EliteDesk",      "EA"),
    ("MAT-IT-003", "Server Dell PowerEdge",     "EA"),
    ("MAT-HW-001", "Network Switch Cisco",      "EA"),
    ("MAT-HW-002", "UPS APC 3KVA",             "EA"),
    ("MAT-HW-003", "Printer HP LaserJet",       "EA"),
    ("MAT-SW-001", "SAP S/4HANA License",       "LIC"),
    ("MAT-SW-002", "Microsoft Office 365",      "LIC"),
    ("MAT-SW-003", "Oracle DB Enterprise",      "LIC"),
    ("MAT-SW-004", "Adobe Creative Cloud",      "LIC"),
    ("MAT-SVC-001", "IT Consulting Services",   "AU"),
    ("MAT-SVC-002", "Cloud Hosting Annual",     "AU"),
    ("MAT-SVC-003", "Managed Support Services", "AU"),
    ("MAT-SVC-004", "Data Migration Project",   "AU"),
    ("MAT-SVC-005", "Training & Certification", "AU"),
]

# Map material → unit price (INR)
MAT_PRICE = {
    "MAT-IT-001": 85000, "MAT-IT-002": 55000, "MAT-IT-003": 350000,
    "MAT-HW-001": 45000, "MAT-HW-002": 28000, "MAT-HW-003": 18000,
    "MAT-SW-001": 500000, "MAT-SW-002": 12000, "MAT-SW-003": 250000, "MAT-SW-004": 8000,
    "MAT-SVC-001": 800000, "MAT-SVC-002": 600000, "MAT-SVC-003": 450000,
    "MAT-SVC-004": 1200000, "MAT-SVC-005": 150000,
}

PAYMENT_TERMS = ["N030", "N045", "N060", "N090"]
GL_ACCOUNTS = {"expense": "400000", "asset": "300000", "tax": "175000", "vendor": "160000"}
COST_CENTERS = {"1000": ["CC1000", "CC1001", "CC1002"], "2000": ["CC2000", "CC2001"], "3000": ["CC3000", "CC3001"]}
USERS = ["FCLERK01", "FCLERK02", "FCLERK03", "FCLERK04", "FCLERK05"]
WAREHOUSES = ["WHOUSE01", "WHOUSE02", "WHOUSE03"]


def clear_sap_tables(session):
    """Clear existing SAP data in correct FK order"""
    print("  Clearing existing SAP data...")
    session.query(MSEG).delete()
    session.query(MKPF).delete()
    session.query(BSEG).delete()
    session.query(BKPF).delete()
    session.query(RSEG).delete()
    session.query(RBKP).delete()
    session.query(EKPO).delete()
    session.query(EKKO).delete()
    session.query(LFB1).delete()
    session.query(LFA1).delete()
    session.commit()
    print("  Done.")


def seed_vendors(session):
    """15 vendors + 3 company codes each = 45 LFB1 records"""
    lfa1_list = []
    for lifnr, name, land, stcd, ktokk in VENDORS:
        lfa1_list.append(LFA1(LIFNR=lifnr, NAME1=name, LAND1=land, STCD1=stcd, KTOKK=ktokk))
    session.add_all(lfa1_list)
    session.flush()

    lfb1_list = []
    for i, (lifnr, *_) in enumerate(VENDORS):
        for bukrs in COMPANY_CODES:
            lfb1_list.append(LFB1(
                LIFNR=lifnr, BUKRS=bukrs,
                AKONT=GL_ACCOUNTS["vendor"],
                ZTERM=PAYMENT_TERMS[i % len(PAYMENT_TERMS)]
            ))
    session.add_all(lfb1_list)
    session.flush()
    print(f"  LFA1: {len(lfa1_list)} vendors | LFB1: {len(lfb1_list)} company code records")


def seed_purchase_orders(session):
    """30 POs with 2 line items each = 60 EKPO records"""
    ekko_list = []
    ekpo_list = []

    base_date = date(2025, 1, 1)
    po_num = 4500001001

    for i in range(30):
        vendor = VENDORS[i % len(VENDORS)]
        lifnr = vendor[0]
        bukrs = COMPANY_CODES[i % len(COMPANY_CODES)]
        po_date = base_date + timedelta(days=i * 7)
        waers = "USD" if i % 5 == 0 else "INR"

        # Pick 2 materials for this PO
        mat1 = MATERIALS[i % len(MATERIALS)]
        mat2 = MATERIALS[(i + 3) % len(MATERIALS)]
        qty1 = (i % 5) + 1
        qty2 = (i % 3) + 1
        price1 = MAT_PRICE[mat1[0]] * (0.85 if waers == "USD" else 1)
        price2 = MAT_PRICE[mat2[0]] * (0.85 if waers == "USD" else 1)
        netwr = (qty1 * price1) + (qty2 * price2)

        ebeln = str(po_num + i)
        ekko_list.append(EKKO(
            EBELN=ebeln, BUKRS=bukrs, LIFNR=lifnr,
            BEDAT=po_date, WAERS=waers, NETWR=round(netwr, 2)
        ))
        ekpo_list.append(EKPO(
            EBELN=ebeln, EBELP="00010",
            MATNR=mat1[0], MENGE=float(qty1), MEINS=mat1[2],
            NETPR=round(price1, 2), NETWR=round(qty1 * price1, 2)
        ))
        ekpo_list.append(EKPO(
            EBELN=ebeln, EBELP="00020",
            MATNR=mat2[0], MENGE=float(qty2), MEINS=mat2[2],
            NETPR=round(price2, 2), NETWR=round(qty2 * price2, 2)
        ))

    session.add_all(ekko_list)
    session.flush()
    session.add_all(ekpo_list)
    session.flush()
    print(f"  EKKO: {len(ekko_list)} PO headers | EKPO: {len(ekpo_list)} PO line items")
    return ekko_list, ekpo_list


def seed_invoices(session, ekko_list, ekpo_list):
    """30 invoices (one per PO) with 2 line items each = 60 RSEG records"""
    rbkp_list = []
    rseg_list = []

    inv_num = 5100000001
    for i, po in enumerate(ekko_list):
        inv_date = po.BEDAT + timedelta(days=10)
        post_date = inv_date + timedelta(days=2)
        gst_rate = 0.18

        # Get PO items for this PO
        po_items = [p for p in ekpo_list if p.EBELN == po.EBELN]
        gross = sum(p.NETWR for p in po_items) * (1 + gst_rate)

        belnr = str(inv_num + i)
        rbkp_list.append(RBKP(
            BELNR=belnr, GJAHR="2025",
            BLDAT=inv_date, BUDAT=post_date,
            LIFNR=po.LIFNR,
            XBLNR=f"EXT-INV-{belnr[-6:]}",
            WAERS=po.WAERS,
            RMWWR=round(gross, 2)
        ))

        for j, po_item in enumerate(po_items):
            rseg_list.append(RSEG(
                BELNR=belnr, GJAHR="2025",
                BUZEI=f"{(j+1):03d}",
                EBELN=po_item.EBELN, EBELP=po_item.EBELP,
                MATNR=po_item.MATNR,
                MENGE=po_item.MENGE,
                WRBTR=po_item.NETWR,
                BWTAR=""
            ))

    session.add_all(rbkp_list)
    session.flush()
    session.add_all(rseg_list)
    session.flush()
    print(f"  RBKP: {len(rbkp_list)} invoice headers | RSEG: {len(rseg_list)} invoice lines")
    return rbkp_list


def seed_accounting(session, rbkp_list):
    """30 accounting headers with 3 lines each = 90 BSEG records"""
    bkpf_list = []
    bseg_list = []

    acc_num = 1400000001
    for i, inv in enumerate(rbkp_list):
        bukrs = COMPANY_CODES[i % len(COMPANY_CODES)]
        belnr = str(acc_num + i)
        blart = "RE"  # Vendor invoice
        cc_list = COST_CENTERS.get(bukrs, ["CC1000"])
        kostl = cc_list[i % len(cc_list)]
        user = USERS[i % len(USERS)]

        net = round(inv.RMWWR / 1.18, 2)
        tax = round(inv.RMWWR - net, 2)

        bkpf_list.append(BKPF(
            BUKRS=bukrs, BELNR=belnr, GJAHR="2025",
            BLART=blart, BUDAT=inv.BUDAT, CPUDT=inv.BUDAT,
            USNAM=user
        ))
        # Vendor credit line
        bseg_list.append(BSEG(
            BUKRS=bukrs, BELNR=belnr, GJAHR="2025", BUZEI="001",
            KOART="K", SHKZG="H",
            WRBTR=inv.RMWWR, DMBTR=inv.RMWWR,
            HKONT=GL_ACCOUNTS["vendor"], KOSTL=""
        ))
        # Expense debit line
        bseg_list.append(BSEG(
            BUKRS=bukrs, BELNR=belnr, GJAHR="2025", BUZEI="002",
            KOART="S", SHKZG="S",
            WRBTR=net, DMBTR=net,
            HKONT=GL_ACCOUNTS["expense"], KOSTL=kostl
        ))
        # Tax debit line
        bseg_list.append(BSEG(
            BUKRS=bukrs, BELNR=belnr, GJAHR="2025", BUZEI="003",
            KOART="S", SHKZG="S",
            WRBTR=tax, DMBTR=tax,
            HKONT=GL_ACCOUNTS["tax"], KOSTL=""
        ))

    session.add_all(bkpf_list)
    session.flush()
    session.add_all(bseg_list)
    session.flush()
    print(f"  BKPF: {len(bkpf_list)} acctg headers | BSEG: {len(bseg_list)} acctg lines")


def seed_material_docs(session, ekko_list, ekpo_list):
    """20 goods receipt docs with 2 lines each = 40 MSEG records"""
    mkpf_list = []
    mseg_list = []

    mat_num = 5000000001
    # Only create GR for first 20 POs
    for i, po in enumerate(ekko_list[:20]):
        gr_date = po.BEDAT + timedelta(days=14)
        mblnr = str(mat_num + i)
        whouse = WAREHOUSES[i % len(WAREHOUSES)]

        mkpf_list.append(MKPF(
            MBLNR=mblnr, MJAHR="2025",
            BLDAT=gr_date, BUDAT=gr_date,
            USNAM=whouse
        ))

        po_items = [p for p in ekpo_list if p.EBELN == po.EBELN]
        for j, po_item in enumerate(po_items):
            werks = po.BUKRS  # Plant = company code for simplicity
            mseg_list.append(MSEG(
                MBLNR=mblnr, MJAHR="2025",
                ZEILE=f"{(j+1):04d}",
                MATNR=po_item.MATNR,
                WERKS=werks,
                MENGE=po_item.MENGE,
                MEINS=po_item.MEINS,
                EBELN=po_item.EBELN,
                EBELP=po_item.EBELP
            ))

    session.add_all(mkpf_list)
    session.flush()
    session.add_all(mseg_list)
    session.flush()
    print(f"  MKPF: {len(mkpf_list)} material doc headers | MSEG: {len(mseg_list)} material doc lines")


def print_summary(session):
    print("\n" + "="*50)
    print("  FINAL RECORD COUNTS")
    print("="*50)
    total = 0
    for model, name in [
        (LFA1, "LFA1  - Vendor Master"),
        (LFB1, "LFB1  - Vendor Co.Code"),
        (EKKO, "EKKO  - PO Headers"),
        (EKPO, "EKPO  - PO Line Items"),
        (RBKP, "RBKP  - Invoice Headers"),
        (RSEG, "RSEG  - Invoice Lines"),
        (BKPF, "BKPF  - Acctg Doc Headers"),
        (BSEG, "BSEG  - Acctg Doc Lines"),
        (MKPF, "MKPF  - Material Doc Headers"),
        (MSEG, "MSEG  - Material Doc Lines"),
    ]:
        count = session.query(model).count()
        total += count
        print(f"  {name}: {count:>4} rows")
    print("-"*50)
    print(f"  TOTAL                   : {total:>4} rows")
    print("="*50)


def verify_fk_integrity(session):
    print("\n  FK Integrity Check:")
    # Every RSEG must have a matching RBKP
    rseg_orphans = session.query(RSEG).filter(
        ~session.query(RBKP).filter(RBKP.BELNR == RSEG.BELNR, RBKP.GJAHR == RSEG.GJAHR).exists()
    ).count()
    print(f"    RSEG orphans (no RBKP parent): {rseg_orphans}")

    # Every EKPO must have a matching EKKO
    ekpo_orphans = session.query(EKPO).filter(
        ~session.query(EKKO).filter(EKKO.EBELN == EKPO.EBELN).exists()
    ).count()
    print(f"    EKPO orphans (no EKKO parent): {ekpo_orphans}")

    # Every BSEG must have a matching BKPF
    bseg_orphans = session.query(BSEG).filter(
        ~session.query(BKPF).filter(
            BKPF.BUKRS == BSEG.BUKRS, BKPF.BELNR == BSEG.BELNR, BKPF.GJAHR == BSEG.GJAHR
        ).exists()
    ).count()
    print(f"    BSEG orphans (no BKPF parent): {bseg_orphans}")

    # Every MSEG must have a matching MKPF
    mseg_orphans = session.query(MSEG).filter(
        ~session.query(MKPF).filter(MKPF.MBLNR == MSEG.MBLNR, MKPF.MJAHR == MSEG.MJAHR).exists()
    ).count()
    print(f"    MSEG orphans (no MKPF parent): {mseg_orphans}")

    if rseg_orphans + ekpo_orphans + bseg_orphans + mseg_orphans == 0:
        print("  ✅ All FK relationships are valid!")
    else:
        print("  ❌ FK integrity issues found!")


def main():
    print("\n" + "="*50)
    print("  SAP Full Data Seeder (100+ records)")
    print("="*50 + "\n")

    session = SessionLocal()
    try:
        clear_sap_tables(session)

        print("Seeding Vendor Master Data...")
        seed_vendors(session)

        print("\nSeeding Purchase Orders...")
        ekko_list, ekpo_list = seed_purchase_orders(session)

        print("\nSeeding Invoices...")
        rbkp_list = seed_invoices(session, ekko_list, ekpo_list)

        print("\nSeeding Accounting Documents...")
        seed_accounting(session, rbkp_list)

        print("\nSeeding Material Documents (Goods Receipts)...")
        seed_material_docs(session, ekko_list, ekpo_list)

        session.commit()

        print_summary(session)
        verify_fk_integrity(session)

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
