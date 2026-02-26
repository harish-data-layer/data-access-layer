# =============================================================
#  push_back/config.py - Configuration for Push Back to SAP
# =============================================================

# SAP Connection (same as whole_sap)
SAP = {
    "host":     "s1.mncinfosys.com",
    "ip":       "49.205.65.5",
    "port":     "44329",
    "protocol": "https",
    "client":   "100",
    "username": "alagan",
    "password": "hana@123",
    "timeout":  120,
}

# PostgreSQL Connection
PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "tai_data_api_db",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
    "schema":   "sap_sap",
}

# API Server
API = {
    "host": "0.0.0.0",
    "port": 5000,
}
