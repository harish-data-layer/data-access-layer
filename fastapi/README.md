# TAI FastAPI Gateway

A FastAPI-based gateway that acts as a **secure middleman** between the AI team and SAP.

## 🏗️ Architecture

```
AI Team  ──POST──▶  FastAPI Gateway (port 8001)  ──▶  Custom SAP API (port 5000)  ──▶  SAP
                           │
                           ▼
                     PostgreSQL DB
                   schema: fastapi
                   ├── incoming_requests  (all requests)
                   └── validation_errors  (all rejections + reason)
```

## 📁 File Structure

```
fastapi/
├── app.py            ← Main FastAPI application
├── db.py             ← DB layer (schema: fastapi, 2 tables)
├── requirements.txt  ← Python dependencies
├── Dockerfile        ← Container definition
└── README.md         ← This file
```

## 🔒 Security

- `X-API-Key` header required on all endpoints
- IP whitelist enforced in staging/production
- In development mode: IP check is skipped for local testing

## 🚀 Quick Start (Local Testing)

### Option 1: Run directly with Python

```bash
cd fastapi
pip install -r requirements.txt
python app.py
```

Server starts at: http://localhost:8001

### Option 2: Run with Docker Compose (Recommended)

```bash
# From root of the project
docker-compose up --build
```

This starts:
- FastAPI Gateway → http://localhost:8001
- Custom SAP API  → http://localhost:5000

## 📬 Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/health` | None | Health check |
| POST | `/api/v1/invoice` | IP + Key | AI Team: Submit real invoice to SAP |
| POST | `/api/v1/invoice/local` | Key only | Local testing (SAP simulated) |
| GET | `/api/v1/requests` | Key | View all stored requests in DB |
| GET | `/api/v1/errors` | Key | View all error logs in DB |
| GET | `/docs` | None | Swagger UI |

## 🧪 Postman Testing

Import `../postman/TAI_FastAPI_Gateway.postman_collection.json` into Postman.

Run in this order:
1. Health Check
2. Submit Valid Invoice (Local)
3. Submit Invalid Invoice (proves validation)
4. Submit without API Key (proves security)
5. View Stored Requests (proves DB storage)
6. View Error Logs (proves error tracking)

## 🗄️ Database

Schema: `fastapi`

### `fastapi.incoming_requests`
Stores every request from the AI team.

### `fastapi.validation_errors`
Stores every rejected request and the reason why (the "golden error schema").

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTAPI_API_KEY` | `tai-secret-key-2024` | Secret key for X-API-Key header |
| `FASTAPI_ALLOWED_IPS` | `127.0.0.1,::1` | Comma-separated whitelist |
| `SAP_BASE_URL` | `http://localhost:5000` | Custom SAP API URL |
| `DB_HOST` | `4.240.80.20` | PostgreSQL host |
| `NODE_ENV` | `development` | Set to `staging` to enforce IP check |
