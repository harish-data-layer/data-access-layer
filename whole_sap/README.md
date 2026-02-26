# Whole SAP - Full OData Database Pull

This module pulls the **entire SAP database** via OData services into PostgreSQL under a dedicated `whole_sap` schema.

## How It Works

Unlike the `odata/` folder which pulls individual tables (MARA, LFA1, VBAK, EKKO), this module:

1. **Auto-discovers ALL OData services** on the SAP server via the IWFND Catalog Service
2. **Finds every entity set** (table) exposed by each service
3. **Pulls all data** with automatic pagination
4. **Creates tables dynamically** in the `whole_sap` PostgreSQL schema
5. **Tracks progress** so you can resume if interrupted

## Usage

### Step 1: Discover what's available (dry run)
```bash
cd whole_sap
python pull_all.py --discover-only
```

### Step 2: Pull everything
```bash
python pull_all.py
```

### Step 3: Pull a specific service only
```bash
python pull_all.py --service API_PRODUCT_SRV
```

### Step 4: Resume an interrupted pull
```bash
python pull_all.py --resume
```

### Just discover services (without pulling)
```bash
python discover_services.py          # list in terminal
python discover_services.py --save   # save to services.json
```

## Output

All data goes into schema: `whole_sap` in the PostgreSQL database.

Table naming: `{service_name}_{entity_name}` (e.g., `api_product_srv_a_product`)

## Files

| File | Description |
|---|---|
| `config.py` | SAP and PostgreSQL connection settings |
| `discover_services.py` | Service discovery via IWFND Catalog |
| `pull_all.py` | Main script to pull all SAP data |
| `requirements.txt` | Python dependencies |
| `whole_sap.log` | Execution log (auto-created) |
| `pull_progress.json` | Progress tracking (auto-created) |
| `services.json` | Saved service catalog (optional) |

## Schema

All data is stored in the `whole_sap` schema with:
- All columns as `TEXT` type (safe for mixed SAP data)
- `_synced_at` timestamp on every row
- Dynamic table creation based on discovered entities
