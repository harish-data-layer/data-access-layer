# =============================================================
#  RFC Pipeline - Configuration
# =============================================================

SAP_RFC = {
    # Connection from Anna: /H/s1.mncinfosys.com/S/3240
    "ashost":  "s1.mncinfosys.com",   # Application server host
    "sysnr":   "40",                   # System number (3240 = 3200 + 40)
    "client":  "100",                  # SAP client
    "user":    "alagan",               # SAP username
    "passwd":  "hana@123",             # SAP password
    "lang":    "EN",                   # Language
}

PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "tai_data_api_db",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
    "schema":   "real_sap",
}

# Default batch size for RFC_READ_TABLE
RFC_BATCH_SIZE = 5000
