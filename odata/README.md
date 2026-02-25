# OData Pipeline - SAP to PostgreSQL
#
# Pull SAP data via OData REST API (requires OData enabled on SAP server)
#
# USAGE:
#   python odata_pull.py test            <- Test connectivity
#   python odata_pull.py material        <- Pull materials
#   python odata_pull.py vendor          <- Pull vendors
#   python odata_pull.py sales_order     <- Pull sales orders
#   python odata_pull.py purchase_order  <- Pull purchase orders
#
# FILES:
#   config.py           - SAP host, ports, credentials, PG connection
#   sap_odata_client.py - HTTP client (port discovery, pull, push)
#   odata_pull.py       - Main script (pull + save to PostgreSQL)
#
# HOW IT WORKS:
#   1. Tries every port/protocol combo to find active SAP OData service
#   2. Sends HTTP GET to OData entity (e.g. API_PRODUCT_SRV/A_Product)
#   3. SAP returns JSON with records
#   4. Follows pagination (__next links) for large datasets
#   5. Cleans data and loads into PostgreSQL (real_sap schema)
#
# NOTE: If OData ports are blocked, use the GUI method instead:
#   python pull_sap/sap_pull.py MARA
