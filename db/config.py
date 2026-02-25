"""
MASTER CONFIGURATION FILE
Use this file to easily manage your SAP tables and seeding logic.
"""

# 1. TABLE DEFINITIONS
# If you want to add a column, just add it to the corresponding list below.
# Format: {"name": "COLUMN_NAME", "type": "String/Integer/Float/Date", "comment": "Description"}

TABLE_CONFIGS = {
    "lfb1": [
        {"name": "LIFNR", "type": "String(10)", "comment": "Vendor"},
        {"name": "BUKRS", "type": "String(4)", "comment": "Company Code"},
        {"name": "ERDAT", "type": "Date", "comment": "Created On"},
    ],
    "ekko": [
        {"name": "EBELN", "type": "String(10)", "comment": "PO Number"},
        {"name": "BUKRS", "type": "String(4)", "comment": "Company Code"},
        {"name": "LIFNR", "type": "String(10)", "comment": "Vendor"},
        {"name": "WAERS", "type": "String(5)", "comment": "Currency"},
        {"name": "NETWR", "type": "Float", "comment": "Net Value"},
        {"name": "AEDAT", "type": "Date", "comment": "Created On"},
    ],
    "ekpo": [
        {"name": "EBELN", "type": "String(10)", "comment": "PO Number"},
        {"name": "EBELP", "type": "String(5)", "comment": "Item"},
        {"name": "MATNR", "type": "String(18)", "comment": "Material"},
        {"name": "MENGE", "type": "Float", "comment": "Quantity"},
        {"name": "NETPR", "type": "Float", "comment": "Net Price"},
    ],
    "rbkp": [
        {"name": "BELNR", "type": "String(10)", "comment": "Invoice Number"},
        {"name": "GJAHR", "type": "String(4)", "comment": "Fiscal Year"},
        {"name": "BLDAT", "type": "Date", "comment": "Doc Date"},
        {"name": "LIFNR", "type": "String(10)", "comment": "Vendor"},
        {"name": "RMWWR", "type": "Float", "comment": "Invoice Amount"},
    ],
    "rseg": [
        {"name": "BELNR", "type": "String(10)", "comment": "Invoice"},
        {"name": "GJAHR", "type": "String(4)", "comment": "Year"},
        {"name": "BUZEI", "type": "String(6)", "comment": "Item"},
        {"name": "EBELN", "type": "String(10)", "comment": "PO Number"},
        {"name": "WRBTR", "type": "Float", "comment": "Item Amount"},
    ],
    "bkpf": [
        {"name": "BUKRS", "type": "String(4)", "comment": "Company"},
        {"name": "BELNR", "type": "String(10)", "comment": "Doc Number"},
        {"name": "GJAHR", "type": "String(4)", "comment": "Year"},
        {"name": "BLDAT", "type": "Date", "comment": "Doc Date"},
    ],
    "bseg": [
        {"name": "BUKRS", "type": "String(4)", "comment": "Company"},
        {"name": "BELNR", "type": "String(10)", "comment": "Doc Number"},
        {"name": "GJAHR", "type": "String(4)", "comment": "Year"},
        {"name": "BUZEI", "type": "String(3)", "comment": "Line Item"},
        {"name": "DMBTR", "type": "Float", "comment": "Amount"},
    ],
    "mkpf": [
        {"name": "MBLNR", "type": "String(10)", "comment": "Mat Doc"},
        {"name": "MJAHR", "type": "String(4)", "comment": "Year"},
        {"name": "BLDAT", "type": "Date", "comment": "Doc Date"},
    ],
    "mseg": [
        {"name": "MBLNR", "type": "String(10)", "comment": "Mat Doc"},
        {"name": "MJAHR", "type": "String(4)", "comment": "Year"},
        {"name": "ZEILE", "type": "String(4)", "comment": "Item"},
        {"name": "MATNR", "type": "String(18)", "comment": "Material"},
        {"name": "MENGE", "type": "Float", "comment": "Quantity"},
    ]
}

# 2. SEED DATA SAMPLES
# This data will be used by the seeding script.
VENDOR_SAMPLES = [
    {"LIFNR": "V10001", "NAME1": "Enterprise Solutions Inc.", "COUNTRY": "US"},
    {"LIFNR": "V10002", "NAME1": "Global Logistics Ltd.", "COUNTRY": "DE"},
    {"LIFNR": "V10003", "NAME1": "Precision Parts Corp.", "COUNTRY": "JP"},
    {"LIFNR": "V10004", "NAME1": "Modern Manufacturing", "COUNTRY": "IN"},
    {"LIFNR": "V10005", "NAME1": "Quality Supplies Co.", "COUNTRY": "UK"},
]

# 3. SETTINGS
DEFAULT_SEED_COUNT = 500
SCHEMA_NAME = "sap"
