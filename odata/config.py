# =============================================================
#  OData Pipeline - Configuration
# =============================================================

SAP = {
    "host":     "s1.mncinfosys.com",
    "ip":       "49.205.65.5",
    "ports":    ["44329"], 
    "client":   "100",
    "username": "alagan",
    "password": "hana@123",
    "timeout":  10,
}

# OData Service Paths
SERVICES = {
    "material":       "/sap/opu/odata/sap/API_PRODUCT_SRV",
    "mara":           "/sap/opu/odata/sap/API_PRODUCT_SRV",
    "vendor":         "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
    "lfa1":           "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
    "sales_order":    "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
    "vbak":           "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
    "purchase_order": "/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV",
    "ekko":           "/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV",
}

ENTITIES = {
    "material":       "A_Product",
    "mara":           "A_Product",
    "vendor":         "A_BusinessPartner",
    "lfa1":           "A_BusinessPartner",
    "sales_order":    "A_SalesOrder",
    "vbak":           "A_SalesOrder",
    "purchase_order": "A_PurchaseOrder",
    "ekko":           "A_PurchaseOrder",
}

PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "tai_data_api_db",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
    "schema":   "real_sap",
}
