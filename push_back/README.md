# Push Back - Push Data from AI Team to SAP

This module provides a **REST API** for the AI team to push data back to SAP.

## Flow

```
AI Team (VIM)
    |
    | Calls API endpoint with JSON payload
    | (vendor_name, vendor_id, etc.)
    v
Python API (Flask)  -->  Pushes to SAP via OData (POST/PATCH)
    |
    | Logs status to database
    v
sap_sap.push_sap table
(tracks: status, errors, who pushed, when, what payload)
```

## How to Run

```bash
cd push_back
pip install -r requirements.txt
python api.py
```

Server starts at: `http://localhost:5000`

## API Endpoints

### 1. POST /push - Create new record in SAP
```json
POST http://localhost:5000/push
{
    "service_path": "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
    "entity_name": "A_BusinessPartner",
    "mata_id": "VENDOR001",
    "payload": {
        "BusinessPartner": "VENDOR001",
        "BusinessPartnerName": "Test Vendor",
        "BusinessPartnerCategory": "2"
    },
    "pushed_by": "ai_team_harish"
}
```

### 2. POST /push/update - Update existing SAP record
```json
POST http://localhost:5000/push/update
{
    "service_path": "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
    "entity_with_key": "A_BusinessPartner('VENDOR001')",
    "payload": {
        "BusinessPartnerName": "Updated Vendor Name"
    },
    "pushed_by": "ai_team_harish"
}
```

### 3. GET /push/status - View all push statuses
```
GET http://localhost:5000/push/status
GET http://localhost:5000/push/status?status=SUCCESS
GET http://localhost:5000/push/status?status=ERROR
GET http://localhost:5000/push/status?pushed_by=ai_team
```

### 4. GET /push/status/<id> - View single push
```
GET http://localhost:5000/push/status/1
```

## Database Table: sap_sap.push_sap

| Column | Type | Description |
|---|---|---|
| id | SERIAL | Auto ID |
| service_name | TEXT | SAP service name |
| entity_name | TEXT | Entity (e.g. A_BusinessPartner) |
| mata_id | TEXT | Unique SAP key |
| action | TEXT | CREATE or UPDATE |
| request_payload | JSONB | What AI team sent |
| response_data | JSONB | What SAP responded |
| status | TEXT | SUCCESS / FAILED / ERROR / PENDING |
| status_code | INTEGER | HTTP status code |
| error_message | TEXT | Error details if failed |
| pushed_by | TEXT | Who triggered the push |
| created_at | TIMESTAMP | When push was initiated |
| updated_at | TIMESTAMP | Last update time |

## Query Push Status in pgAdmin

```sql
-- All pushes
SELECT * FROM sap_sap.push_sap;

-- Only failures
SELECT * FROM sap_sap.push_sap WHERE status = 'FAILED';

-- Count by status
SELECT status, COUNT(*) FROM sap_sap.push_sap GROUP BY status;
```
