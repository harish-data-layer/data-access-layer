#!/usr/bin/env python3
# =============================================================
#  fastapi/app.py - AI Team FastAPI Gateway (Staging-Ready)
#
#  SECURITY LAYERS:
#    1. IP Whitelist  → only known IPs allowed (staging mode)
#    2. API Key       → X-API-Key header required
#    3. Rate Limiting → max 60 requests/minute per IP
#    4. Docs hidden   → /docs disabled in staging/production
#    5. Error masking → no internal details leaked on error
#
#  ENDPOINTS:
#    POST /api/v1/invoice        - AI team submits invoice to SAP (staging)
#    POST /api/v1/invoice/local  - Local testing invoice (simulates SAP)
#    POST /api/v1/pull           - AI team pulls data FROM SAP (staging)
#    POST /api/v1/pull/local     - Local testing pull (simulates SAP data)
#    GET  /health                - Health check (public)
#    GET  /api/v1/requests       - View stored requests (internal)
#    GET  /api/v1/errors         - View stored errors (internal)
# =============================================================

import os
import uuid
import logging
import time
import requests
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from db import init_db, store_request, store_error, get_all_requests, get_all_errors

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ─── Logging Setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gateway.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("FastAPI-Gateway")

# ─── Config from .env ────────────────────────────────────────
API_KEY      = os.getenv("FASTAPI_API_KEY", "tai-secret-key-2024")
ALLOWED_IPS  = [ip.strip() for ip in os.getenv("FASTAPI_ALLOWED_IPS", "127.0.0.1,::1,localhost").split(",")]
SAP_BASE_URL = os.getenv("SAP_BASE_URL", "http://localhost:5000")
ENVIRONMENT  = os.getenv("NODE_ENV", "development")

# In staging/production: hide Swagger docs
IS_PRODUCTION = ENVIRONMENT in ("staging", "production")

log.info(f"🌍 Environment : {ENVIRONMENT}")
log.info(f"🔒 Docs exposed: {'NO (hidden)' if IS_PRODUCTION else 'YES (dev mode)'}")
log.info(f"🛡️  IP Check    : {'ENABLED' if IS_PRODUCTION else 'DISABLED (dev mode)'}")
log.info(f"🔑 Allowed IPs : {ALLOWED_IPS}")

# ─── Simple In-Memory Rate Limiter ───────────────────────────
# Tracks how many requests each IP made in the last 60 seconds
_rate_store: dict = defaultdict(list)
RATE_LIMIT   = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))   # max 60 req/min per IP

def check_rate_limit(ip: str):
    now = time.time()
    window = 60  # seconds
    # Keep only requests within the last 60 seconds
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < window]
    if len(_rate_store[ip]) >= RATE_LIMIT:
        log.warning(f"🚫 Rate limit exceeded for IP: {ip}")
        raise HTTPException(
            status_code=429,
            detail={"error": "RATE_LIMIT_EXCEEDED", "message": f"Too many requests. Max {RATE_LIMIT}/min allowed."}
        )
    _rate_store[ip].append(now)

# ─── App Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 TAI FastAPI Gateway starting...")
    init_db()
    log.info("✅ Database schema 'fastapi' ready")
    yield
    log.info("🛑 Gateway shutting down")

# ─── FastAPI App ─────────────────────────────────────────────
# In staging: docs_url=None hides /docs from the public internet
app = FastAPI(
    title="TAI FastAPI Gateway",
    description="AI Team ↔ SAP Integration Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

# CORS — restrict to known origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not IS_PRODUCTION else ALLOWED_IPS,
    allow_methods=["*"],
    allow_headers=["X-API-Key", "Content-Type"],
)


# =============================================================
#  MIDDLEWARE — Log every request + response
# =============================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    client_ip = request.client.host
    log.info(f"→ {request.method} {request.url.path} | from {client_ip}")
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    log.info(f"← {response.status_code} | {duration}ms")
    return response


# =============================================================
#  SECURITY — IP + API Key + Rate Limit
# =============================================================
async def validate_access(request: Request, x_api_key: Optional[str] = Header(None)):
    """
    3-layer security check:
    1. Rate limit (all environments)
    2. IP whitelist (staging/production only)
    3. API Key check (all environments)
    """
    client_ip = request.client.host

    # Layer 1: Rate Limit
    check_rate_limit(client_ip)

    # Layer 2: IP Whitelist (only in staging/production)
    if IS_PRODUCTION:
        if client_ip not in ALLOWED_IPS:
            log.warning(f"🚫 BLOCKED IP: {client_ip} — not in whitelist")
            raise HTTPException(
                status_code=403,
                detail={"error": "ACCESS_DENIED", "message": "Your IP is not authorized"}
            )

    # Layer 3: API Key
    if not x_api_key or x_api_key != API_KEY:
        log.warning(f"🔑 INVALID API KEY from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid or missing X-API-Key header"}
        )

    return {"ip": client_ip}


# =============================================================
#  PYDANTIC MODELS — Invoice Validation
# =============================================================

# =============================================================
#  PYDANTIC MODEL — SAP Pull Request
# =============================================================
class SAPPullRequest(BaseModel):
    service_path: str             = Field(..., min_length=1, description="SAP OData service path e.g. /sap/opu/odata/sap/API_SALES_ORDER_SRV")
    entity_name:  str             = Field(..., min_length=1, description="Entity set name e.g. A_SalesOrder")
    filters:      Optional[str]   = Field(None,              description="OData filter e.g. SalesOrderType eq 'OR'")
    top:          Optional[int]   = Field(100, gt=0, le=5000, description="Max records to pull (1-5000)")
    select:       Optional[str]   = Field(None,              description="Comma-separated fields to return")
    save_to_db:   Optional[bool]  = Field(True,              description="Save pulled records to DB?")
    called_by:    Optional[str]   = Field("ai_team",         description="Who is calling")
class InvoiceItem(BaseModel):
    po_number:       str            = Field(..., min_length=1,  description="Purchase Order Number (EBELN)")
    line_item:       str            = Field(..., min_length=1,  description="PO Line Item Number (EBELP)")
    material_number: Optional[str]  = Field(None,              description="Material Number (MATNR)")
    quantity:        float          = Field(..., gt=0,          description="Quantity — must be greater than 0")
    unit:            Optional[str]  = Field("EA",              description="Unit of measure")
    amount:          float          = Field(...,               description="Line item amount")
    currency:        str            = Field("INR", min_length=3, max_length=3, description="3-letter currency code")

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v):
        return v.upper()


class InvoicePayload(BaseModel):
    invoice_number: str            = Field(..., min_length=1,            description="Invoice number (BELNR)")
    vendor_id:      str            = Field(..., min_length=1,            description="Vendor ID (LIFNR)")
    company_code:   str            = Field(..., min_length=1, max_length=4, description="Company Code (BUKRS)")
    fiscal_year:    str            = Field(..., min_length=4, max_length=4, description="Fiscal Year e.g. 2024")
    document_date:  str            = Field(...,                          description="Date in YYYY-MM-DD format")
    total_amount:   float          = Field(...,                          description="Total invoice amount")
    currency:       str            = Field("INR", min_length=3, max_length=3)
    line_items:     List[InvoiceItem] = Field(..., min_length=1,        description="Minimum 1 line item required")
    called_by:      Optional[str]  = Field("ai_team",                   description="Caller identifier")
    notes:          Optional[str]  = Field(None,                        description="Optional notes")
    # Make SAP Service dynamic so AI team can target the correct one once confirmed with SAP team
    service_path:   Optional[str]  = Field("/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV", description="OData API Path")
    entity_name:    Optional[str]  = Field("A_SupplierInvoice",           description="Target OData Entity")

    @field_validator("fiscal_year")
    @classmethod
    def year_digits_only(cls, v):
        if not v.isdigit():
            raise ValueError("fiscal_year must be 4 digits e.g. '2024'")
        return v

    @field_validator("document_date")
    @classmethod
    def valid_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("document_date must be YYYY-MM-DD format e.g. '2024-03-01'")
        return v

    @field_validator("total_amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("total_amount must be a positive number")
        return v

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v):
        return v.upper()


# =============================================================
#  SAP CALLER — Calls our existing Custom Flask API
# =============================================================
def call_sap_invoice(invoice: InvoicePayload) -> dict:
    """Forward validated invoice to SAP via the Custom API."""
    try:
        sap_payload = {
            "service_path": invoice.service_path,
            "entity_name":  invoice.entity_name,
            "mata_id":      invoice.invoice_number,
            "payload": {
                "SupplierInvoice":  invoice.invoice_number,
                "CompanyCode":      invoice.company_code,
                "FiscalYear":       invoice.fiscal_year,
                "DocumentDate":     invoice.document_date,
                "InvoicingParty":   invoice.vendor_id,
                "DocumentCurrency": invoice.currency,
                "InvoiceGrossAmount": str(invoice.total_amount),
            },
            "called_by": invoice.called_by or "fastapi_gateway"
        }

        resp = requests.post(
            f"{SAP_BASE_URL}/push",
            json=sap_payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        return {
            "success":     resp.status_code in (200, 201),
            "status_code": resp.status_code,
            "response":    resp.json() if resp.content else {}
        }
    except requests.exceptions.ConnectionError:
        return {"success": False, "status_code": 503, "response": {"error": "SAP API unreachable"}}
    except requests.exceptions.Timeout:
        return {"success": False, "status_code": 504, "response": {"error": "SAP API timed out (30s)"}}
    except Exception as e:
        return {"success": False, "status_code": 500, "response": {"error": str(e)}}


# =============================================================
#  ENDPOINT 1 — AI Team Invoice (Staging / Production)
#  POST /api/v1/invoice
#  Requires: X-API-Key header + IP whitelist (staging)
# =============================================================
@app.post(
    "/api/v1/invoice",
    summary="Submit Invoice — AI Team (Staging)",
    tags=["AI Team"],
    dependencies=[Depends(validate_access)]
)
async def submit_invoice(invoice: InvoicePayload, request: Request):
    """
    **Main endpoint for AI Team on staging.**

    Security: IP Whitelist + X-API-Key + Rate Limit
    Flow: Receive → Validate → Call SAP → Store in DB
    """
    request_id = str(uuid.uuid4())
    client_ip  = request.client.host
    log.info(f"📥 INVOICE | id={request_id} | from={client_ip} | inv={invoice.invoice_number}")

    # Store immediately — even before SAP call
    store_request(request_id=request_id, source_ip=client_ip,
                  payload=invoice.dict(), status="processing")

    # Call SAP
    sap = call_sap_invoice(invoice)

    if sap["success"]:
        store_request(request_id=request_id, source_ip=client_ip,
                      payload=invoice.dict(), status="success",
                      sap_response=sap["response"])
        log.info(f"✅ Invoice {invoice.invoice_number} → SAP success")
        return JSONResponse(status_code=200, content={
            "request_id":   request_id,
            "status":       "SUCCESS",
            "invoice":      invoice.invoice_number,
            "message":      "Invoice accepted and forwarded to SAP",
            "sap_response": sap["response"]
        })
    else:
        store_request(request_id=request_id, source_ip=client_ip,
                      payload=invoice.dict(), status="failed",
                      sap_response=sap["response"])
        store_error(request_id=request_id,
                    error_code="SAP_CALL_FAILED",
                    error_message=str(sap["response"].get("error", "SAP error")),
                    field_name="sap_integration")
        log.error(f"❌ Invoice {invoice.invoice_number} → SAP failed: {sap['response']}")
        return JSONResponse(status_code=502, content={
            "request_id": request_id,
            "status":     "FAILED",
            "message":    "Invoice stored but SAP call failed — check /api/v1/errors",
            "error_code": "SAP_CALL_FAILED"
            # Note: no internal error details exposed to caller in staging
        })


# =============================================================
#  ENDPOINT 2 — Local Testing
#  POST /api/v1/invoice/local
#  Requires: X-API-Key header only (no IP check, SAP simulated)
# =============================================================
@app.post(
    "/api/v1/invoice/local",
    summary="Submit Invoice — Local Test (SAP Simulated)",
    tags=["Local Testing"],
)
async def submit_invoice_local(
    invoice: InvoicePayload,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    **Use this for local testing and Postman demos.**

    - API Key required (no IP check)
    - SAP is NOT actually called — response is simulated
    - All data is still stored in DB
    - Proves end-to-end flow: receive → validate → store
    """
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid or missing X-API-Key header"}
        )

    request_id = str(uuid.uuid4())
    client_ip  = request.client.host
    log.info(f"🧪 LOCAL TEST | id={request_id} | inv={invoice.invoice_number}")

    # Simulate what SAP would return
    simulated_sap = {
        "status":           "SUCCESS (SIMULATED — SAP not called in local mode)",
        "invoice_number":   invoice.invoice_number,
        "vendor_id":        invoice.vendor_id,
        "company_code":     invoice.company_code,
        "total_amount":     invoice.total_amount,
        "currency":         invoice.currency,
        "line_items_count": len(invoice.line_items),
        "timestamp":        datetime.utcnow().isoformat()
    }

    store_request(
        request_id=request_id,
        source_ip=f"{client_ip} [LOCAL_TEST]",
        payload=invoice.dict(),
        status="local_test",
        sap_response=simulated_sap
    )

    return JSONResponse(status_code=200, content={
        "request_id":          request_id,
        "status":              "SUCCESS",
        "mode":                "LOCAL_TEST",
        "validation_passed":   True,
        "db_stored":           True,
        "sap_called":          False,
        "message":             f"Invoice {invoice.invoice_number} validated ✅ | Stored in DB ✅ | SAP simulated ⚡",
        "simulated_sap":       simulated_sap,
    })


# =============================================================
#  ENDPOINT 3 — AI Team PULL from SAP (Staging / Production)
#  POST /api/v1/pull
#  Requires: X-API-Key header + IP whitelist (staging)
# =============================================================
@app.post(
    "/api/v1/pull",
    summary="Pull SAP Data — AI Team (Staging)",
    tags=["AI Team"],
    dependencies=[Depends(validate_access)]
)
async def pull_sap_data(pull_req: SAPPullRequest, request: Request):
    """
    **AI Team pulls data FROM SAP through our gateway.**

    Security: IP Whitelist + X-API-Key + Rate Limit
    Flow: Receive → Validate → Call Custom SAP API /pull → Return data + Log in DB
    """
    request_id = str(uuid.uuid4())
    client_ip  = request.client.host
    log.info(f"📤 PULL | id={request_id} | from={client_ip} | entity={pull_req.entity_name}")

    # Log the pull request immediately
    pull_payload = pull_req.dict()
    store_request(
        request_id=request_id,
        source_ip=client_ip,
        payload={**pull_payload, "operation": "PULL"},
        status="processing"
    )

    try:
        sap_payload = {
            "service_path": pull_req.service_path,
            "entity_name":  pull_req.entity_name,
            "top":          pull_req.top,
            "save_to_db":   pull_req.save_to_db,
            "called_by":    pull_req.called_by or "fastapi_gateway",
        }
        if pull_req.filters:
            sap_payload["filters"] = pull_req.filters
        if pull_req.select:
            sap_payload["select"] = pull_req.select

        resp = requests.post(
            f"{SAP_BASE_URL}/pull",
            json=sap_payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        sap_result = resp.json() if resp.content else {}

        if resp.status_code == 200 and sap_result.get("status") == "SUCCESS":
            data = sap_result.get("data", [])
            
            # Save to sap_sap.sap_pull_fastapi table
            if data and pull_req.save_to_db:
                from db import save_fastapi_pulled_data
                save_fastapi_pulled_data(pull_req.service_path, pull_req.entity_name, data)
                
            store_request(
                request_id=request_id,
                source_ip=client_ip,
                payload={**pull_payload, "operation": "PULL"},
                status="success",
                sap_response={"records_count": sap_result.get("records_count", 0)}
            )
            log.info(f"✅ PULL success | {sap_result.get('records_count', 0)} records | entity={pull_req.entity_name}")
            return JSONResponse(status_code=200, content={
                "request_id":    request_id,
                "status":        "SUCCESS",
                "operation":     "PULL",
                "entity":        pull_req.entity_name,
                "records_count": sap_result.get("records_count", 0),
                "saved_to_db":   sap_result.get("saved_to_db", 0),
                "data":          sap_result.get("data", []),
            })
        else:
            store_request(
                request_id=request_id,
                source_ip=client_ip,
                payload={**pull_payload, "operation": "PULL"},
                status="failed",
                sap_response=sap_result
            )
            store_error(
                request_id=request_id,
                error_code="SAP_PULL_FAILED",
                error_message=str(sap_result.get("error", "SAP pull error")),
                field_name="sap_integration",
                raw_payload=pull_payload
            )
            log.error(f"❌ PULL failed | entity={pull_req.entity_name} | {sap_result}")
            return JSONResponse(status_code=502, content={
                "request_id": request_id,
                "status":     "FAILED",
                "operation":  "PULL",
                "message":    "SAP pull failed — check /api/v1/errors",
                "error_code": "SAP_PULL_FAILED"
            })

    except requests.exceptions.ConnectionError:
        store_request(request_id=request_id, source_ip=client_ip,
                      payload={**pull_payload, "operation": "PULL"}, status="failed",
                      sap_response={"error": "SAP API unreachable"})
        return JSONResponse(status_code=503, content={"request_id": request_id, "status": "FAILED", "error": "SAP API unreachable"})
    except Exception as e:
        store_request(request_id=request_id, source_ip=client_ip,
                      payload={**pull_payload, "operation": "PULL"}, status="failed",
                      sap_response={"error": str(e)})
        return JSONResponse(status_code=500, content={"request_id": request_id, "status": "FAILED", "error": "Internal error"})


# =============================================================
#  ENDPOINT 4 — Local PULL Test (SAP Simulated)
#  POST /api/v1/pull/local
#  Requires: X-API-Key only (no IP check, SAP simulated)
# =============================================================
@app.post(
    "/api/v1/pull/local",
    summary="Pull SAP Data — Local Test (Simulated)",
    tags=["Local Testing"],
)
async def pull_sap_data_local(
    pull_req: SAPPullRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    **Use this for local testing — SAP data is simulated.**

    - API Key required (no IP check)
    - Returns mock SAP data so you can test without real SAP connection
    - Pull request is still logged in DB
    """
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid or missing X-API-Key header"}
        )

    request_id = str(uuid.uuid4())
    client_ip  = request.client.host
    log.info(f"🧪 LOCAL PULL | id={request_id} | entity={pull_req.entity_name}")

    # Simulated SAP data
    simulated_records = [
        {"id": 1, "entity": pull_req.entity_name, "field1": "SIMULATED_VALUE_001", "field2": 10000, "currency": "INR"},
        {"id": 2, "entity": pull_req.entity_name, "field1": "SIMULATED_VALUE_002", "field2": 20000, "currency": "INR"},
        {"id": 3, "entity": pull_req.entity_name, "field1": "SIMULATED_VALUE_003", "field2": 30000, "currency": "INR"},
    ]

    store_request(
        request_id=request_id,
        source_ip=f"{client_ip} [LOCAL_TEST]",
        payload={**pull_req.dict(), "operation": "PULL_LOCAL"},
        status="local_test",
        sap_response={"records_count": len(simulated_records), "simulated": True}
    )

    return JSONResponse(status_code=200, content={
        "request_id":    request_id,
        "status":        "SUCCESS",
        "mode":          "LOCAL_TEST",
        "operation":     "PULL",
        "entity":        pull_req.entity_name,
        "service_path":  pull_req.service_path,
        "filters_used":  pull_req.filters,
        "records_count": len(simulated_records),
        "sap_called":    False,
        "message":       f"Simulated {len(simulated_records)} records from {pull_req.entity_name} ⚡",
        "data":          simulated_records,
    })


# =============================================================
#  GET /api/v1/requests — View all stored requests
# =============================================================
@app.get("/api/v1/requests", summary="View Stored Requests", tags=["Monitoring"])
async def list_requests(
    status:    Optional[str] = None,
    limit:     int = 50,
    x_api_key: Optional[str] = Header(None)
):
    """View all requests stored in `fastapi.incoming_requests`. Requires API key."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    rows = get_all_requests(status=status, limit=limit)
    return {
        "total":    len(rows),
        "schema":   "fastapi.incoming_requests",
        "requests": rows
    }


# =============================================================
#  GET /api/v1/errors — View all validation/SAP errors
# =============================================================
@app.get("/api/v1/errors", summary="View Error Logs", tags=["Monitoring"])
async def list_errors(
    limit:     int = 50,
    x_api_key: Optional[str] = Header(None)
):
    """View all errors stored in `fastapi.validation_errors`. Requires API key."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    rows = get_all_errors(limit=limit)
    return {
        "total":  len(rows),
        "schema": "fastapi.validation_errors",
        "errors": rows
    }


# =============================================================
#  GET /health — Public health check
# =============================================================
@app.get("/health", tags=["System"], summary="Health Check")
async def health():
    """Public health check — no auth needed. Use this to verify the server is up."""
    return {
        "status":      "running",
        "service":     "TAI FastAPI Gateway",
        "version":     "1.0.0",
        "environment": ENVIRONMENT,
        "ip_check":    IS_PRODUCTION,
        "docs_visible": not IS_PRODUCTION,
        "timestamp":   datetime.utcnow().isoformat()
    }


# =============================================================
#  Run (development only — production uses docker-compose)
# =============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
