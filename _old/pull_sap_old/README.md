# SAP ↔ PostgreSQL Sync Pipeline

This pipeline allows pulling material data from SAP S/4HANA OData API into a PostgreSQL cloud database and pushing updates back.

## Project Structure
- `main.py`: Main entry point.
- `sap_client.py`: API client for SAP.
- `db.py`: Database management (uses schema `sap`).
- `sync_materials.py`: Material-specific mapping logic.
- `config.py`: SAP and Database credentials.

## Setup
```bash
pip install -r requirements.txt
```

## Usage
- **Pull all materials**: `python main.py pull`
- **Pull specific type**: `python main.py pull FERT`
- **Push all to SAP**: `python main.py push`
- **Push specific record**: `python main.py push MAT001`

## Database View
Data is stored in the **`sap`** schema. You can view it in pgAdmin under:
`Databases > postgres > Schemas > sap > Tables > MARA`
