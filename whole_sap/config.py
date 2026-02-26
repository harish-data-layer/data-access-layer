# =============================================================
#  whole_sap/config.py - Configuration for Full SAP OData Pull
# =============================================================

# SAP Connection
SAP = {
    "host":     "s1.mncinfosys.com",
    "ip":       "49.205.65.5",
    "port":     "44329",          # HTTPS port (confirmed working)
    "protocol": "https",
    "client":   "100",
    "username": "alagan",
    "password": "hana@123",
    "timeout":  30,               # longer timeout for large pulls
}

# PostgreSQL Connection
PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "tai_data_api_db",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
    "schema":   "sap_sap",        # new schema for full SAP data
}

# OData Catalog endpoint - this returns ALL available services on the SAP server
CATALOG_URL = "/sap/opu/odata/IWFND/CATALOGSERVICE;v=2"

# Max records per entity (safety limit per entity set)
MAX_RECORDS_PER_ENTITY = 50000

# Batch size for PostgreSQL inserts
PG_BATCH_SIZE = 500

# Services to SKIP (system/internal services you don't want to pull)
SKIP_SERVICES = {
    "CATALOGSERVICE",
    "IWFND_SB_ADMIN_SRV",
    "INTEROP_SRV",
}

# If you only want to pull specific services, list them here.
# Leave empty [] to pull ALL discovered services.
ONLY_SERVICES = []
