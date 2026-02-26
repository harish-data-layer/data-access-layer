#!/usr/bin/env python3
# =============================================================
#  push_back/api.py - REST API for AI Team to Push Data to SAP
#
#  The AI team calls these endpoints with JSON payload.
#  The API pushes to SAP and logs status in push_sap table.
#
#  USAGE:
#    python api.py
#
#  ENDPOINTS:
#    POST /push          - Push data to SAP (create new record)
#    POST /push/update   - Update existing SAP record
#    GET  /push/status   - View all push operations & status
#    GET  /push/status/<id> - View single push status
#    GET  /health        - Health check
#
#  EXAMPLE CALL (AI team sends this):
#    POST http://localhost:5000/push
#    {
#      "service_path": "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
#      "entity_name": "A_BusinessPartner",
#      "payload": {
#        "BusinessPartner": "VENDOR001",
#        "BusinessPartnerName": "Test Vendor",
#        "BusinessPartnerCategory": "2"
#      },
#      "pushed_by": "ai_team_harish"
#    }
# =============================================================

import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify
from sap_push import SAPPushClient, log_push
from db_setup import setup as setup_db
from config import SAP, PG, API

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("PushAPI")

app = Flask(__name__)
sap_client = SAPPushClient()


# =============================================================
#  POST /push - Create new record in SAP
# =============================================================
@app.route("/push", methods=["POST"])
def push_to_sap():
    """
    AI team calls this endpoint to push data to SAP.

    Request JSON:
    {
        "service_path": "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
        "entity_name": "A_BusinessPartner",
        "mata_id": "VENDOR001",          (optional - auto-detected if not given)
        "payload": {
            "BusinessPartner": "VENDOR001",
            "BusinessPartnerName": "Test Vendor"
        },
        "pushed_by": "ai_team"           (optional)
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    # Required fields
    service_path = data.get("service_path")
    entity_name  = data.get("entity_name")
    payload      = data.get("payload")

    if not service_path:
        return jsonify({"error": "Missing 'service_path'"}), 400
    if not entity_name:
        return jsonify({"error": "Missing 'entity_name'"}), 400
    if not payload:
        return jsonify({"error": "Missing 'payload'"}), 400

    mata_id   = data.get("mata_id", "")
    pushed_by = data.get("pushed_by", "ai_team")

    # Extract service name from path for logging
    service_name = service_path.rstrip("/").split("/")[-1]

    log.info(f"PUSH CREATE: {service_name}/{entity_name} by {pushed_by}")

    # Push to SAP
    result = sap_client.push_create(service_path, entity_name, payload)

    # Log to push_sap table
    push_id = log_push(
        service_name=service_name,
        entity_name=entity_name,
        mata_id=mata_id,
        action="CREATE",
        request_payload=payload,
        status=result["status"],
        status_code=result["status_code"],
        response_data=result["response_data"],
        error_message=result["error_message"],
        pushed_by=pushed_by,
    )

    return jsonify({
        "push_id": push_id,
        "status": result["status"],
        "status_code": result["status_code"],
        "message": f"Push {'successful' if result['status'] == 'SUCCESS' else 'failed'}",
        "error": result["error_message"],
        "response": result["response_data"],
    }), 200 if result["status"] == "SUCCESS" else 500


# =============================================================
#  POST /push/update - Update existing SAP record
# =============================================================
@app.route("/push/update", methods=["POST"])
def push_update_sap():
    """
    AI team calls this to UPDATE an existing SAP record.

    Request JSON:
    {
        "service_path": "/sap/opu/odata/sap/API_BUSINESS_PARTNER",
        "entity_with_key": "A_BusinessPartner('VENDOR001')",
        "payload": {
            "BusinessPartnerName": "Updated Vendor Name"
        },
        "pushed_by": "ai_team"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    service_path    = data.get("service_path")
    entity_with_key = data.get("entity_with_key")
    payload         = data.get("payload")

    if not service_path:
        return jsonify({"error": "Missing 'service_path'"}), 400
    if not entity_with_key:
        return jsonify({"error": "Missing 'entity_with_key' (e.g. A_Product('MAT001'))"}), 400
    if not payload:
        return jsonify({"error": "Missing 'payload'"}), 400

    pushed_by    = data.get("pushed_by", "ai_team")
    service_name = service_path.rstrip("/").split("/")[-1]

    # Extract entity name and key from entity_with_key
    entity_name = entity_with_key.split("(")[0] if "(" in entity_with_key else entity_with_key
    mata_id     = data.get("mata_id", "")

    log.info(f"PUSH UPDATE: {service_name}/{entity_with_key} by {pushed_by}")

    # Push to SAP
    result = sap_client.push_update(service_path, entity_with_key, payload)

    # Log to push_sap table
    push_id = log_push(
        service_name=service_name,
        entity_name=entity_name,
        mata_id=mata_id,
        action="UPDATE",
        request_payload=payload,
        status=result["status"],
        status_code=result["status_code"],
        response_data=result["response_data"],
        error_message=result["error_message"],
        pushed_by=pushed_by,
    )

    return jsonify({
        "push_id": push_id,
        "status": result["status"],
        "status_code": result["status_code"],
        "message": f"Update {'successful' if result['status'] == 'SUCCESS' else 'failed'}",
        "error": result["error_message"],
        "response": result["response_data"],
    }), 200 if result["status"] == "SUCCESS" else 500


# =============================================================
#  GET /push/status - View all push operations
# =============================================================
@app.route("/push/status", methods=["GET"])
def get_push_status():
    """
    View all push operations with their status.

    Query params:
        ?status=SUCCESS     - filter by status
        ?entity=A_Product   - filter by entity
        ?pushed_by=ai_team  - filter by who pushed
        ?limit=50           - limit results
    """
    schema    = PG["schema"]
    status    = request.args.get("status")
    entity    = request.args.get("entity")
    pushed_by = request.args.get("pushed_by")
    limit     = request.args.get("limit", 100, type=int)

    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = f"SELECT * FROM {schema}.push_sap WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status.upper())
            if entity:
                query += " AND entity_name = %s"
                params.append(entity)
            if pushed_by:
                query += " AND pushed_by = %s"
                params.append(pushed_by)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

            # Convert datetime to string
            for row in rows:
                for key, val in row.items():
                    if isinstance(val, datetime):
                        row[key] = val.isoformat()

            # Summary counts
            cur.execute(f"""
                SELECT status, COUNT(*) as count
                FROM {schema}.push_sap
                GROUP BY status
            """)
            summary = {r["status"]: r["count"] for r in cur.fetchall()}

            return jsonify({
                "total": len(rows),
                "summary": summary,
                "records": rows,
            })

    finally:
        conn.close()


# =============================================================
#  GET /push/status/<id> - View single push status
# =============================================================
@app.route("/push/status/<int:push_id>", methods=["GET"])
def get_push_status_by_id(push_id):
    """View a single push operation by ID."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {schema}.push_sap WHERE id = %s", (push_id,))
            row = cur.fetchone()

            if not row:
                return jsonify({"error": f"Push ID {push_id} not found"}), 404

            for key, val in row.items():
                if isinstance(val, datetime):
                    row[key] = val.isoformat()

            return jsonify(row)
    finally:
        conn.close()


# =============================================================
#  GET /health - Health check
# =============================================================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "service": "SAP Push Back API",
        "sap_host": SAP["host"],
        "db_schema": PG["schema"],
        "timestamp": datetime.now().isoformat(),
    })


# =============================================================
#  START
# =============================================================
if __name__ == "__main__":
    # Setup database table on startup
    log.info("Setting up push_sap table...")
    setup_db()

    log.info(f"Starting Push Back API on {API['host']}:{API['port']}")
    log.info(f"Endpoints:")
    log.info(f"  POST /push           - Push new record to SAP")
    log.info(f"  POST /push/update    - Update existing SAP record")
    log.info(f"  GET  /push/status    - View all push statuses")
    log.info(f"  GET  /push/status/1  - View single push status")
    log.info(f"  GET  /health         - Health check")

    app.run(host=API["host"], port=API["port"], debug=True)
