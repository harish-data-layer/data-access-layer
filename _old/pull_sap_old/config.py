# =============================================================
#  config.py — SAP + PostgreSQL Configuration
# =============================================================

# ── SAP S/4HANA Settings ─────────────────────────────────────
SAP = {
    "base_url":  "http://s1.mncinfosys.com:8040",  # S/4HANA Instance on port 8040 (instance 40)
    "client":    "100",
    "username":  "alagan",
    "password":  "hana@123",
    "timeout":   120,
}

# ── PostgreSQL (Cloud) Settings ───────────────────────────────
POSTGRES = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "postgres",
    "username": "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

# ── SAP OData Service Paths ───────────────────────────────────
SAP_SERVICES = {
    "material":          "/sap/opu/odata/sap/API_PRODUCT_SRV",
    "sales_order":       "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
    "purchase_order":    "/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV",
    "business_partner":  "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
}

# ── Sync Settings ─────────────────────────────────────────────
SYNC = {
    "batch_size":    500,
    "max_sap_rows":  5000,
    "log_file":      "sap_sync.log",
}
