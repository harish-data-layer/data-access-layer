# TAI Data API - SAP ↔ PostgreSQL Sync Pipeline

This pipeline provides a **hybrid synchronization** method for pulling material data from SAP S/4HANA:
1. **OData API**: Primary method (fastest, requires open ports).
2. **SAP GUI Fallback**: Secondary method (automated via COM scripting, works if API ports are blocked).

## Features
- Hybrid connectivity testing (checks ports 8000, 8040, 3240, 3340, etc.)
- Automatic fallback to SAP GUI SE16N extraction if API fails.
- Intelligent field mapping between OData JSON and GUI Technical Names (MATNR, MTART, etc.)
- PostgreSQL cloud integration with Upsert logic.
