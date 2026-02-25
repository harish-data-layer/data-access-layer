# =============================================================
#  OData Pipeline - Configuration
# =============================================================

SAP = {
    "host":     "s1.mncinfosys.com",
    "ip":       "49.205.65.5",
    "ports":    ["8040", "8000", "443", "3240", "3340", "8140", "44340"],
    "client":   "100",
    "username": "alagan",
    "password": "hana@123",
    "timeout":  30,
}

# OData Service Paths (add more as needed)
SERVICES = {
    "material":     "/sap/opu/odata/sap/API_PRODUCT_SRV",
    "vendor":       "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
    "sales_order":  "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
    "purchase_order": "/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV",
}

# Entity sets within each service
ENTITIES = {
    "material":       "A_Product",
    "vendor":         "A_BusinessPartner",
    "sales_order":    "A_SalesOrder",
    "purchase_order": "A_PurchaseOrder",
}

PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "tai_data_api_db",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
    "schema":   "real_sap",
}
