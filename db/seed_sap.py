"""
SAP Sample Data Seeder
Populates all 10 SAP tables with realistic test data.
Run: python -m db.seed_sap
"""
from datetime import date, datetime
from db.base import SessionLocal
from db.models.sap_tables import RBKP, RSEG, BKPF, BSEG, LFA1, LFB1, EKKO, EKPO, MKPF, MSEG


def seed_lfa1(session):
    """Vendor Master Data - 10 vendors"""
    vendors = [
        LFA1(LIFNR="V001", NAME1="Tata Consultancy Services", LAND1="IN", STCD1="27AABCT1332L1ZV", KTOKK="KRED"),
        LFA1(LIFNR="V002", NAME1="Infosys Limited", LAND1="IN", STCD1="29AABCI1681G1ZK", KTOKK="KRED"),
        LFA1(LIFNR="V003", NAME1="Wipro Technologies", LAND1="IN", STCD1="29AAACW0867H1ZQ", KTOKK="KRED"),
        LFA1(LIFNR="V004", NAME1="HCL Technologies", LAND1="IN", STCD1="09AAACH1645R1ZE", KTOKK="KRED"),
        LFA1(LIFNR="V005", NAME1="Tech Mahindra Ltd", LAND1="IN", STCD1="27AABCT3518Q1ZF", KTOKK="KRED"),
        LFA1(LIFNR="V006", NAME1="SAP India Pvt Ltd", LAND1="IN", STCD1="29AABCS4259H1ZU", KTOKK="KRED"),
        LFA1(LIFNR="V007", NAME1="Oracle India Pvt Ltd", LAND1="IN", STCD1="29AABCO0538N1ZX", KTOKK="KRED"),
        LFA1(LIFNR="V008", NAME1="Microsoft India Pvt Ltd", LAND1="IN", STCD1="29AABCM4011G1ZR", KTOKK="KRED"),
        LFA1(LIFNR="V009", NAME1="IBM India Pvt Ltd", LAND1="IN", STCD1="29AABCI0638B1ZD", KTOKK="KRED"),
        LFA1(LIFNR="V010", NAME1="Accenture Solutions Pvt Ltd", LAND1="IN", STCD1="29AABCA3678M1ZT", KTOKK="KRED"),
    ]
    existing = session.query(LFA1).count()
    if existing == 0:
        session.add_all(vendors)
        print(f"  Seeded {len(vendors)} LFA1 (Vendor Master) records")
    else:
        print(f"  LFA1 already has {existing} records, skipping")


def seed_lfb1(session):
    """Vendor Company Code Data"""
    records = [
        LFB1(LIFNR="V001", BUKRS="1000", AKONT="160000", ZTERM="N030"),
        LFB1(LIFNR="V002", BUKRS="1000", AKONT="160000", ZTERM="N045"),
        LFB1(LIFNR="V003", BUKRS="1000", AKONT="160000", ZTERM="N030"),
        LFB1(LIFNR="V004", BUKRS="1000", AKONT="160000", ZTERM="N060"),
        LFB1(LIFNR="V005", BUKRS="1000", AKONT="160000", ZTERM="N030"),
        LFB1(LIFNR="V006", BUKRS="2000", AKONT="160000", ZTERM="N045"),
        LFB1(LIFNR="V007", BUKRS="2000", AKONT="160000", ZTERM="N030"),
        LFB1(LIFNR="V008", BUKRS="2000", AKONT="160000", ZTERM="N060"),
        LFB1(LIFNR="V009", BUKRS="3000", AKONT="160000", ZTERM="N030"),
        LFB1(LIFNR="V010", BUKRS="3000", AKONT="160000", ZTERM="N045"),
    ]
    existing = session.query(LFB1).count()
    if existing == 0:
        session.add_all(records)
        print(f"  Seeded {len(records)} LFB1 (Vendor Company Code) records")
    else:
        print(f"  LFB1 already has {existing} records, skipping")


def seed_ekko(session):
    """Purchase Order Headers - 15 POs"""
    pos = [
        EKKO(EBELN="4500001001", BUKRS="1000", LIFNR="V001", BEDAT=date(2025, 1, 10), WAERS="INR", NETWR=500000.00),
        EKKO(EBELN="4500001002", BUKRS="1000", LIFNR="V002", BEDAT=date(2025, 1, 15), WAERS="INR", NETWR=750000.00),
        EKKO(EBELN="4500001003", BUKRS="1000", LIFNR="V003", BEDAT=date(2025, 2, 1), WAERS="INR", NETWR=320000.00),
        EKKO(EBELN="4500001004", BUKRS="1000", LIFNR="V004", BEDAT=date(2025, 2, 10), WAERS="INR", NETWR=980000.00),
        EKKO(EBELN="4500001005", BUKRS="2000", LIFNR="V005", BEDAT=date(2025, 2, 20), WAERS="INR", NETWR=450000.00),
        EKKO(EBELN="4500001006", BUKRS="2000", LIFNR="V006", BEDAT=date(2025, 3, 1), WAERS="USD", NETWR=12000.00),
        EKKO(EBELN="4500001007", BUKRS="2000", LIFNR="V007", BEDAT=date(2025, 3, 5), WAERS="USD", NETWR=25000.00),
        EKKO(EBELN="4500001008", BUKRS="3000", LIFNR="V008", BEDAT=date(2025, 3, 15), WAERS="USD", NETWR=18500.00),
        EKKO(EBELN="4500001009", BUKRS="3000", LIFNR="V009", BEDAT=date(2025, 4, 1), WAERS="INR", NETWR=620000.00),
        EKKO(EBELN="4500001010", BUKRS="3000", LIFNR="V010", BEDAT=date(2025, 4, 10), WAERS="INR", NETWR=890000.00),
        EKKO(EBELN="4500001011", BUKRS="1000", LIFNR="V001", BEDAT=date(2025, 4, 20), WAERS="INR", NETWR=340000.00),
        EKKO(EBELN="4500001012", BUKRS="1000", LIFNR="V003", BEDAT=date(2025, 5, 1), WAERS="INR", NETWR=560000.00),
        EKKO(EBELN="4500001013", BUKRS="2000", LIFNR="V005", BEDAT=date(2025, 5, 10), WAERS="INR", NETWR=720000.00),
        EKKO(EBELN="4500001014", BUKRS="2000", LIFNR="V007", BEDAT=date(2025, 5, 20), WAERS="USD", NETWR=31000.00),
        EKKO(EBELN="4500001015", BUKRS="3000", LIFNR="V009", BEDAT=date(2025, 6, 1), WAERS="INR", NETWR=410000.00),
    ]
    existing = session.query(EKKO).count()
    if existing == 0:
        session.add_all(pos)
        print(f"  Seeded {len(pos)} EKKO (PO Header) records")
    else:
        print(f"  EKKO already has {existing} records, skipping")


def seed_ekpo(session):
    """Purchase Order Line Items - 30 items"""
    items = [
        EKPO(EBELN="4500001001", EBELP="00010", MATNR="MAT-IT-001", MENGE=10.0, MEINS="EA", NETPR=50000.0, NETWR=500000.0),
        EKPO(EBELN="4500001002", EBELP="00010", MATNR="MAT-SW-001", MENGE=5.0, MEINS="LIC", NETPR=100000.0, NETWR=500000.0),
        EKPO(EBELN="4500001002", EBELP="00020", MATNR="MAT-SW-002", MENGE=5.0, MEINS="LIC", NETPR=50000.0, NETWR=250000.0),
        EKPO(EBELN="4500001003", EBELP="00010", MATNR="MAT-HW-001", MENGE=20.0, MEINS="EA", NETPR=16000.0, NETWR=320000.0),
        EKPO(EBELN="4500001004", EBELP="00010", MATNR="MAT-SVC-001", MENGE=1.0, MEINS="AU", NETPR=980000.0, NETWR=980000.0),
        EKPO(EBELN="4500001005", EBELP="00010", MATNR="MAT-IT-002", MENGE=15.0, MEINS="EA", NETPR=30000.0, NETWR=450000.0),
        EKPO(EBELN="4500001006", EBELP="00010", MATNR="MAT-SW-003", MENGE=10.0, MEINS="LIC", NETPR=1200.0, NETWR=12000.0),
        EKPO(EBELN="4500001007", EBELP="00010", MATNR="MAT-SW-004", MENGE=5.0, MEINS="LIC", NETPR=5000.0, NETWR=25000.0),
        EKPO(EBELN="4500001008", EBELP="00010", MATNR="MAT-SW-005", MENGE=1.0, MEINS="LIC", NETPR=18500.0, NETWR=18500.0),
        EKPO(EBELN="4500001009", EBELP="00010", MATNR="MAT-SVC-002", MENGE=1.0, MEINS="AU", NETPR=620000.0, NETWR=620000.0),
        EKPO(EBELN="4500001010", EBELP="00010", MATNR="MAT-SVC-003", MENGE=1.0, MEINS="AU", NETPR=890000.0, NETWR=890000.0),
        EKPO(EBELN="4500001011", EBELP="00010", MATNR="MAT-HW-002", MENGE=10.0, MEINS="EA", NETPR=34000.0, NETWR=340000.0),
        EKPO(EBELN="4500001012", EBELP="00010", MATNR="MAT-IT-003", MENGE=8.0, MEINS="EA", NETPR=70000.0, NETWR=560000.0),
        EKPO(EBELN="4500001013", EBELP="00010", MATNR="MAT-SVC-004", MENGE=1.0, MEINS="AU", NETPR=720000.0, NETWR=720000.0),
        EKPO(EBELN="4500001014", EBELP="00010", MATNR="MAT-SW-006", MENGE=1.0, MEINS="LIC", NETPR=31000.0, NETWR=31000.0),
        EKPO(EBELN="4500001015", EBELP="00010", MATNR="MAT-SVC-005", MENGE=1.0, MEINS="AU", NETPR=410000.0, NETWR=410000.0),
    ]
    existing = session.query(EKPO).count()
    if existing == 0:
        session.add_all(items)
        print(f"  Seeded {len(items)} EKPO (PO Line Items) records")
    else:
        print(f"  EKPO already has {existing} records, skipping")


def seed_rbkp(session):
    """Invoice Document Headers - 20 invoices"""
    invoices = [
        RBKP(BELNR="5100000001", GJAHR="2025", BLDAT=date(2025, 1, 20), BUDAT=date(2025, 1, 22), LIFNR="V001", XBLNR="TCS-INV-2501", WAERS="INR", RMWWR=590000.00),
        RBKP(BELNR="5100000002", GJAHR="2025", BLDAT=date(2025, 1, 25), BUDAT=date(2025, 1, 27), LIFNR="V002", XBLNR="INF-INV-2501", WAERS="INR", RMWWR=885000.00),
        RBKP(BELNR="5100000003", GJAHR="2025", BLDAT=date(2025, 2, 5), BUDAT=date(2025, 2, 7), LIFNR="V003", XBLNR="WIP-INV-2502", WAERS="INR", RMWWR=377600.00),
        RBKP(BELNR="5100000004", GJAHR="2025", BLDAT=date(2025, 2, 15), BUDAT=date(2025, 2, 17), LIFNR="V004", XBLNR="HCL-INV-2502", WAERS="INR", RMWWR=1156400.00),
        RBKP(BELNR="5100000005", GJAHR="2025", BLDAT=date(2025, 2, 25), BUDAT=date(2025, 2, 27), LIFNR="V005", XBLNR="TM-INV-2502", WAERS="INR", RMWWR=531000.00),
        RBKP(BELNR="5100000006", GJAHR="2025", BLDAT=date(2025, 3, 5), BUDAT=date(2025, 3, 7), LIFNR="V006", XBLNR="SAP-INV-2503", WAERS="USD", RMWWR=14160.00),
        RBKP(BELNR="5100000007", GJAHR="2025", BLDAT=date(2025, 3, 10), BUDAT=date(2025, 3, 12), LIFNR="V007", XBLNR="ORA-INV-2503", WAERS="USD", RMWWR=29500.00),
        RBKP(BELNR="5100000008", GJAHR="2025", BLDAT=date(2025, 3, 20), BUDAT=date(2025, 3, 22), LIFNR="V008", XBLNR="MS-INV-2503", WAERS="USD", RMWWR=21830.00),
        RBKP(BELNR="5100000009", GJAHR="2025", BLDAT=date(2025, 4, 5), BUDAT=date(2025, 4, 7), LIFNR="V009", XBLNR="IBM-INV-2504", WAERS="INR", RMWWR=731600.00),
        RBKP(BELNR="5100000010", GJAHR="2025", BLDAT=date(2025, 4, 15), BUDAT=date(2025, 4, 17), LIFNR="V010", XBLNR="ACC-INV-2504", WAERS="INR", RMWWR=1050200.00),
        RBKP(BELNR="5100000011", GJAHR="2025", BLDAT=date(2025, 4, 25), BUDAT=date(2025, 4, 27), LIFNR="V001", XBLNR="TCS-INV-2504", WAERS="INR", RMWWR=401200.00),
        RBKP(BELNR="5100000012", GJAHR="2025", BLDAT=date(2025, 5, 5), BUDAT=date(2025, 5, 7), LIFNR="V002", XBLNR="INF-INV-2505", WAERS="INR", RMWWR=660800.00),
        RBKP(BELNR="5100000013", GJAHR="2025", BLDAT=date(2025, 5, 15), BUDAT=date(2025, 5, 17), LIFNR="V003", XBLNR="WIP-INV-2505", WAERS="INR", RMWWR=848000.00),
        RBKP(BELNR="5100000014", GJAHR="2025", BLDAT=date(2025, 5, 25), BUDAT=date(2025, 5, 27), LIFNR="V005", XBLNR="TM-INV-2505", WAERS="INR", RMWWR=483600.00),
        RBKP(BELNR="5100000015", GJAHR="2025", BLDAT=date(2025, 6, 5), BUDAT=date(2025, 6, 7), LIFNR="V007", XBLNR="ORA-INV-2506", WAERS="USD", RMWWR=36580.00),
        RBKP(BELNR="5100000016", GJAHR="2025", BLDAT=date(2025, 6, 15), BUDAT=date(2025, 6, 17), LIFNR="V009", XBLNR="IBM-INV-2506", WAERS="INR", RMWWR=483800.00),
        RBKP(BELNR="5100000017", GJAHR="2025", BLDAT=date(2025, 7, 5), BUDAT=date(2025, 7, 7), LIFNR="V004", XBLNR="HCL-INV-2507", WAERS="INR", RMWWR=920000.00),
        RBKP(BELNR="5100000018", GJAHR="2025", BLDAT=date(2025, 7, 15), BUDAT=date(2025, 7, 17), LIFNR="V006", XBLNR="SAP-INV-2507", WAERS="USD", RMWWR=9440.00),
        RBKP(BELNR="5100000019", GJAHR="2025", BLDAT=date(2025, 8, 5), BUDAT=date(2025, 8, 7), LIFNR="V010", XBLNR="ACC-INV-2508", WAERS="INR", RMWWR=1062400.00),
        RBKP(BELNR="5100000020", GJAHR="2025", BLDAT=date(2025, 8, 15), BUDAT=date(2025, 8, 17), LIFNR="V001", XBLNR="TCS-INV-2508", WAERS="INR", RMWWR=295400.00),
    ]
    existing = session.query(RBKP).count()
    if existing == 0:
        session.add_all(invoices)
        print(f"  Seeded {len(invoices)} RBKP (Invoice Header) records")
    else:
        print(f"  RBKP already has {existing} records, skipping")


def seed_rseg(session):
    """Invoice Line Items - 30 lines"""
    lines = [
        RSEG(BELNR="5100000001", GJAHR="2025", BUZEI="001", EBELN="4500001001", EBELP="00010", MATNR="MAT-IT-001", MENGE=10.0, WRBTR=500000.0, BWTAR=""),
        RSEG(BELNR="5100000002", GJAHR="2025", BUZEI="001", EBELN="4500001002", EBELP="00010", MATNR="MAT-SW-001", MENGE=5.0, WRBTR=500000.0, BWTAR=""),
        RSEG(BELNR="5100000002", GJAHR="2025", BUZEI="002", EBELN="4500001002", EBELP="00020", MATNR="MAT-SW-002", MENGE=5.0, WRBTR=250000.0, BWTAR=""),
        RSEG(BELNR="5100000003", GJAHR="2025", BUZEI="001", EBELN="4500001003", EBELP="00010", MATNR="MAT-HW-001", MENGE=20.0, WRBTR=320000.0, BWTAR=""),
        RSEG(BELNR="5100000004", GJAHR="2025", BUZEI="001", EBELN="4500001004", EBELP="00010", MATNR="MAT-SVC-001", MENGE=1.0, WRBTR=980000.0, BWTAR=""),
        RSEG(BELNR="5100000005", GJAHR="2025", BUZEI="001", EBELN="4500001005", EBELP="00010", MATNR="MAT-IT-002", MENGE=15.0, WRBTR=450000.0, BWTAR=""),
        RSEG(BELNR="5100000006", GJAHR="2025", BUZEI="001", EBELN="4500001006", EBELP="00010", MATNR="MAT-SW-003", MENGE=10.0, WRBTR=12000.0, BWTAR=""),
        RSEG(BELNR="5100000007", GJAHR="2025", BUZEI="001", EBELN="4500001007", EBELP="00010", MATNR="MAT-SW-004", MENGE=5.0, WRBTR=25000.0, BWTAR=""),
        RSEG(BELNR="5100000008", GJAHR="2025", BUZEI="001", EBELN="4500001008", EBELP="00010", MATNR="MAT-SW-005", MENGE=1.0, WRBTR=18500.0, BWTAR=""),
        RSEG(BELNR="5100000009", GJAHR="2025", BUZEI="001", EBELN="4500001009", EBELP="00010", MATNR="MAT-SVC-002", MENGE=1.0, WRBTR=620000.0, BWTAR=""),
        RSEG(BELNR="5100000010", GJAHR="2025", BUZEI="001", EBELN="4500001010", EBELP="00010", MATNR="MAT-SVC-003", MENGE=1.0, WRBTR=890000.0, BWTAR=""),
        RSEG(BELNR="5100000011", GJAHR="2025", BUZEI="001", EBELN="4500001011", EBELP="00010", MATNR="MAT-HW-002", MENGE=10.0, WRBTR=340000.0, BWTAR=""),
        RSEG(BELNR="5100000012", GJAHR="2025", BUZEI="001", EBELN="4500001012", EBELP="00010", MATNR="MAT-IT-003", MENGE=8.0, WRBTR=560000.0, BWTAR=""),
        RSEG(BELNR="5100000013", GJAHR="2025", BUZEI="001", EBELN="4500001013", EBELP="00010", MATNR="MAT-SVC-004", MENGE=1.0, WRBTR=720000.0, BWTAR=""),
        RSEG(BELNR="5100000014", GJAHR="2025", BUZEI="001", EBELN="4500001015", EBELP="00010", MATNR="MAT-SVC-005", MENGE=1.0, WRBTR=410000.0, BWTAR=""),
        RSEG(BELNR="5100000015", GJAHR="2025", BUZEI="001", EBELN="4500001014", EBELP="00010", MATNR="MAT-SW-006", MENGE=1.0, WRBTR=31000.0, BWTAR=""),
        RSEG(BELNR="5100000016", GJAHR="2025", BUZEI="001", EBELN="4500001009", EBELP="00010", MATNR="MAT-SVC-002", MENGE=1.0, WRBTR=410000.0, BWTAR=""),
        RSEG(BELNR="5100000017", GJAHR="2025", BUZEI="001", EBELN="4500001004", EBELP="00010", MATNR="MAT-SVC-001", MENGE=1.0, WRBTR=780000.0, BWTAR=""),
        RSEG(BELNR="5100000018", GJAHR="2025", BUZEI="001", EBELN="4500001006", EBELP="00010", MATNR="MAT-SW-003", MENGE=4.0, WRBTR=8000.0, BWTAR=""),
        RSEG(BELNR="5100000019", GJAHR="2025", BUZEI="001", EBELN="4500001010", EBELP="00010", MATNR="MAT-SVC-003", MENGE=1.0, WRBTR=900000.0, BWTAR=""),
        RSEG(BELNR="5100000020", GJAHR="2025", BUZEI="001", EBELN="4500001001", EBELP="00010", MATNR="MAT-IT-001", MENGE=5.0, WRBTR=250000.0, BWTAR=""),
    ]
    existing = session.query(RSEG).count()
    if existing == 0:
        session.add_all(lines)
        print(f"  Seeded {len(lines)} RSEG (Invoice Line Items) records")
    else:
        print(f"  RSEG already has {existing} records, skipping")


def seed_bkpf(session):
    """Accounting Document Headers - 20 records"""
    docs = [
        BKPF(BUKRS="1000", BELNR="1400000001", GJAHR="2025", BLART="RE", BUDAT=date(2025, 1, 22), CPUDT=date(2025, 1, 22), USNAM="FCLERK01"),
        BKPF(BUKRS="1000", BELNR="1400000002", GJAHR="2025", BLART="RE", BUDAT=date(2025, 1, 27), CPUDT=date(2025, 1, 27), USNAM="FCLERK01"),
        BKPF(BUKRS="1000", BELNR="1400000003", GJAHR="2025", BLART="RE", BUDAT=date(2025, 2, 7), CPUDT=date(2025, 2, 7), USNAM="FCLERK02"),
        BKPF(BUKRS="1000", BELNR="1400000004", GJAHR="2025", BLART="RE", BUDAT=date(2025, 2, 17), CPUDT=date(2025, 2, 17), USNAM="FCLERK02"),
        BKPF(BUKRS="2000", BELNR="1400000005", GJAHR="2025", BLART="RE", BUDAT=date(2025, 2, 27), CPUDT=date(2025, 2, 27), USNAM="FCLERK03"),
        BKPF(BUKRS="2000", BELNR="1400000006", GJAHR="2025", BLART="RE", BUDAT=date(2025, 3, 7), CPUDT=date(2025, 3, 7), USNAM="FCLERK03"),
        BKPF(BUKRS="2000", BELNR="1400000007", GJAHR="2025", BLART="RE", BUDAT=date(2025, 3, 12), CPUDT=date(2025, 3, 12), USNAM="FCLERK04"),
        BKPF(BUKRS="2000", BELNR="1400000008", GJAHR="2025", BLART="RE", BUDAT=date(2025, 3, 22), CPUDT=date(2025, 3, 22), USNAM="FCLERK04"),
        BKPF(BUKRS="3000", BELNR="1400000009", GJAHR="2025", BLART="RE", BUDAT=date(2025, 4, 7), CPUDT=date(2025, 4, 7), USNAM="FCLERK05"),
        BKPF(BUKRS="3000", BELNR="1400000010", GJAHR="2025", BLART="RE", BUDAT=date(2025, 4, 17), CPUDT=date(2025, 4, 17), USNAM="FCLERK05"),
        BKPF(BUKRS="1000", BELNR="1400000011", GJAHR="2025", BLART="ZP", BUDAT=date(2025, 2, 20), CPUDT=date(2025, 2, 20), USNAM="FCLERK01"),
        BKPF(BUKRS="1000", BELNR="1400000012", GJAHR="2025", BLART="ZP", BUDAT=date(2025, 2, 28), CPUDT=date(2025, 2, 28), USNAM="FCLERK02"),
        BKPF(BUKRS="2000", BELNR="1400000013", GJAHR="2025", BLART="ZP", BUDAT=date(2025, 3, 25), CPUDT=date(2025, 3, 25), USNAM="FCLERK03"),
        BKPF(BUKRS="2000", BELNR="1400000014", GJAHR="2025", BLART="ZP", BUDAT=date(2025, 4, 5), CPUDT=date(2025, 4, 5), USNAM="FCLERK04"),
        BKPF(BUKRS="3000", BELNR="1400000015", GJAHR="2025", BLART="ZP", BUDAT=date(2025, 4, 25), CPUDT=date(2025, 4, 25), USNAM="FCLERK05"),
        BKPF(BUKRS="1000", BELNR="1400000016", GJAHR="2025", BLART="RE", BUDAT=date(2025, 5, 7), CPUDT=date(2025, 5, 7), USNAM="FCLERK01"),
        BKPF(BUKRS="1000", BELNR="1400000017", GJAHR="2025", BLART="RE", BUDAT=date(2025, 5, 17), CPUDT=date(2025, 5, 17), USNAM="FCLERK02"),
        BKPF(BUKRS="2000", BELNR="1400000018", GJAHR="2025", BLART="RE", BUDAT=date(2025, 6, 7), CPUDT=date(2025, 6, 7), USNAM="FCLERK03"),
        BKPF(BUKRS="3000", BELNR="1400000019", GJAHR="2025", BLART="RE", BUDAT=date(2025, 7, 7), CPUDT=date(2025, 7, 7), USNAM="FCLERK05"),
        BKPF(BUKRS="3000", BELNR="1400000020", GJAHR="2025", BLART="ZP", BUDAT=date(2025, 8, 7), CPUDT=date(2025, 8, 7), USNAM="FCLERK05"),
    ]
    existing = session.query(BKPF).count()
    if existing == 0:
        session.add_all(docs)
        print(f"  Seeded {len(docs)} BKPF (Accounting Doc Header) records")
    else:
        print(f"  BKPF already has {existing} records, skipping")


def seed_bseg(session):
    """Accounting Document Segments - 30 lines"""
    lines = [
        BSEG(BUKRS="1000", BELNR="1400000001", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=590000.0, DMBTR=590000.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000001", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=500000.0, DMBTR=500000.0, HKONT="400000", KOSTL="CC1000"),
        BSEG(BUKRS="1000", BELNR="1400000001", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=90000.0, DMBTR=90000.0, HKONT="175000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000002", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=885000.0, DMBTR=885000.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000002", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=750000.0, DMBTR=750000.0, HKONT="400000", KOSTL="CC1001"),
        BSEG(BUKRS="1000", BELNR="1400000002", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=135000.0, DMBTR=135000.0, HKONT="175000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000003", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=377600.0, DMBTR=377600.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000003", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=320000.0, DMBTR=320000.0, HKONT="300000", KOSTL="CC1002"),
        BSEG(BUKRS="1000", BELNR="1400000003", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=57600.0, DMBTR=57600.0, HKONT="175000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000004", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=1156400.0, DMBTR=1156400.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="1000", BELNR="1400000004", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=980000.0, DMBTR=980000.0, HKONT="400000", KOSTL="CC1003"),
        BSEG(BUKRS="1000", BELNR="1400000004", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=176400.0, DMBTR=176400.0, HKONT="175000", KOSTL=""),
        BSEG(BUKRS="2000", BELNR="1400000005", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=531000.0, DMBTR=531000.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="2000", BELNR="1400000005", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=450000.0, DMBTR=450000.0, HKONT="400000", KOSTL="CC2000"),
        BSEG(BUKRS="2000", BELNR="1400000005", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=81000.0, DMBTR=81000.0, HKONT="175000", KOSTL=""),
        BSEG(BUKRS="2000", BELNR="1400000006", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=14160.0, DMBTR=1180000.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="2000", BELNR="1400000006", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=12000.0, DMBTR=1000000.0, HKONT="400000", KOSTL="CC2001"),
        BSEG(BUKRS="2000", BELNR="1400000006", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=2160.0, DMBTR=180000.0, HKONT="175000", KOSTL=""),
        BSEG(BUKRS="3000", BELNR="1400000009", GJAHR="2025", BUZEI="001", KOART="K", SHKZG="H", WRBTR=731600.0, DMBTR=731600.0, HKONT="160000", KOSTL=""),
        BSEG(BUKRS="3000", BELNR="1400000009", GJAHR="2025", BUZEI="002", KOART="S", SHKZG="S", WRBTR=620000.0, DMBTR=620000.0, HKONT="400000", KOSTL="CC3000"),
        BSEG(BUKRS="3000", BELNR="1400000009", GJAHR="2025", BUZEI="003", KOART="S", SHKZG="S", WRBTR=111600.0, DMBTR=111600.0, HKONT="175000", KOSTL=""),
    ]
    existing = session.query(BSEG).count()
    if existing == 0:
        session.add_all(lines)
        print(f"  Seeded {len(lines)} BSEG (Accounting Doc Segment) records")
    else:
        print(f"  BSEG already has {existing} records, skipping")


def seed_mkpf(session):
    """Material Document Headers - 10 records"""
    docs = [
        MKPF(MBLNR="5000000001", MJAHR="2025", BLDAT=date(2025, 1, 25), BUDAT=date(2025, 1, 25), USNAM="WHOUSE01"),
        MKPF(MBLNR="5000000002", MJAHR="2025", BLDAT=date(2025, 2, 10), BUDAT=date(2025, 2, 10), USNAM="WHOUSE01"),
        MKPF(MBLNR="5000000003", MJAHR="2025", BLDAT=date(2025, 2, 20), BUDAT=date(2025, 2, 20), USNAM="WHOUSE02"),
        MKPF(MBLNR="5000000004", MJAHR="2025", BLDAT=date(2025, 3, 5), BUDAT=date(2025, 3, 5), USNAM="WHOUSE02"),
        MKPF(MBLNR="5000000005", MJAHR="2025", BLDAT=date(2025, 3, 20), BUDAT=date(2025, 3, 20), USNAM="WHOUSE01"),
        MKPF(MBLNR="5000000006", MJAHR="2025", BLDAT=date(2025, 4, 10), BUDAT=date(2025, 4, 10), USNAM="WHOUSE03"),
        MKPF(MBLNR="5000000007", MJAHR="2025", BLDAT=date(2025, 4, 25), BUDAT=date(2025, 4, 25), USNAM="WHOUSE03"),
        MKPF(MBLNR="5000000008", MJAHR="2025", BLDAT=date(2025, 5, 10), BUDAT=date(2025, 5, 10), USNAM="WHOUSE01"),
        MKPF(MBLNR="5000000009", MJAHR="2025", BLDAT=date(2025, 6, 5), BUDAT=date(2025, 6, 5), USNAM="WHOUSE02"),
        MKPF(MBLNR="5000000010", MJAHR="2025", BLDAT=date(2025, 7, 1), BUDAT=date(2025, 7, 1), USNAM="WHOUSE03"),
    ]
    existing = session.query(MKPF).count()
    if existing == 0:
        session.add_all(docs)
        print(f"  Seeded {len(docs)} MKPF (Material Doc Header) records")
    else:
        print(f"  MKPF already has {existing} records, skipping")


def seed_mseg(session):
    """Material Document Line Items - 20 records"""
    lines = [
        MSEG(MBLNR="5000000001", MJAHR="2025", ZEILE="0001", MATNR="MAT-IT-001", WERKS="1000", MENGE=10.0, MEINS="EA", EBELN="4500001001", EBELP="00010"),
        MSEG(MBLNR="5000000002", MJAHR="2025", ZEILE="0001", MATNR="MAT-SW-001", WERKS="1000", MENGE=5.0, MEINS="LIC", EBELN="4500001002", EBELP="00010"),
        MSEG(MBLNR="5000000002", MJAHR="2025", ZEILE="0002", MATNR="MAT-SW-002", WERKS="1000", MENGE=5.0, MEINS="LIC", EBELN="4500001002", EBELP="00020"),
        MSEG(MBLNR="5000000003", MJAHR="2025", ZEILE="0001", MATNR="MAT-HW-001", WERKS="1000", MENGE=20.0, MEINS="EA", EBELN="4500001003", EBELP="00010"),
        MSEG(MBLNR="5000000004", MJAHR="2025", ZEILE="0001", MATNR="MAT-IT-002", WERKS="2000", MENGE=15.0, MEINS="EA", EBELN="4500001005", EBELP="00010"),
        MSEG(MBLNR="5000000005", MJAHR="2025", ZEILE="0001", MATNR="MAT-SW-003", WERKS="2000", MENGE=10.0, MEINS="LIC", EBELN="4500001006", EBELP="00010"),
        MSEG(MBLNR="5000000006", MJAHR="2025", ZEILE="0001", MATNR="MAT-SW-004", WERKS="2000", MENGE=5.0, MEINS="LIC", EBELN="4500001007", EBELP="00010"),
        MSEG(MBLNR="5000000007", MJAHR="2025", ZEILE="0001", MATNR="MAT-SW-005", WERKS="3000", MENGE=1.0, MEINS="LIC", EBELN="4500001008", EBELP="00010"),
        MSEG(MBLNR="5000000008", MJAHR="2025", ZEILE="0001", MATNR="MAT-HW-002", WERKS="1000", MENGE=10.0, MEINS="EA", EBELN="4500001011", EBELP="00010"),
        MSEG(MBLNR="5000000009", MJAHR="2025", ZEILE="0001", MATNR="MAT-IT-003", WERKS="1000", MENGE=8.0, MEINS="EA", EBELN="4500001012", EBELP="00010"),
        MSEG(MBLNR="5000000010", MJAHR="2025", ZEILE="0001", MATNR="MAT-SW-006", WERKS="2000", MENGE=1.0, MEINS="LIC", EBELN="4500001014", EBELP="00010"),
    ]
    existing = session.query(MSEG).count()
    if existing == 0:
        session.add_all(lines)
        print(f"  Seeded {len(lines)} MSEG (Material Doc Line Items) records")
    else:
        print(f"  MSEG already has {existing} records, skipping")


def main():
    print("\n========================================")
    print("  SAP Sample Data Seeder")
    print("========================================\n")

    session = SessionLocal()
    try:
        print("Seeding Vendor Master Data...")
        seed_lfa1(session)
        seed_lfb1(session)
        session.commit()

        print("\nSeeding Purchase Order Data...")
        seed_ekko(session)
        seed_ekpo(session)
        session.commit()

        print("\nSeeding Invoice Data...")
        seed_rbkp(session)
        seed_rseg(session)
        session.commit()

        print("\nSeeding Accounting Data...")
        seed_bkpf(session)
        seed_bseg(session)
        session.commit()

        print("\nSeeding Material Document Data...")
        seed_mkpf(session)
        seed_mseg(session)
        session.commit()

        print("\n========================================")
        print("  SAP Seeding Complete!")
        print("========================================")
        print("\nRecord counts:")
        for model, name in [(LFA1, "LFA1 Vendors"), (LFB1, "LFB1 Vendor Co.Code"),
                            (EKKO, "EKKO PO Headers"), (EKPO, "EKPO PO Items"),
                            (RBKP, "RBKP Invoice Headers"), (RSEG, "RSEG Invoice Lines"),
                            (BKPF, "BKPF Acctg Headers"), (BSEG, "BSEG Acctg Lines"),
                            (MKPF, "MKPF Material Docs"), (MSEG, "MSEG Material Lines")]:
            count = session.query(model).count()
            print(f"  {name}: {count} rows")

    except Exception as e:
        session.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
