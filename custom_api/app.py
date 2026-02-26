#!/usr/bin/env python3
# =============================================================
#  custom_api/app.py - Custom Data API
#
#  ONE API for EVERYTHING:
#    - Pull data from ANY SAP service
#    - Push data to ANY SAP service
#    - Discover all services
#    - Track all operations
#
#  USAGE:
#    python app.py
#    Server runs at http://localhost:5000
#
#  ENDPOINTS:
#    GET  /services                 - List all SAP services
#    GET  /services/<name>/entities - List entities in a service
#
#    POST /pull                     - Pull data from SAP
#    POST /push                     - Create new record in SAP
#    POST /push/update              - Update record in SAP
#
#    GET  /logs                     - View all operation logs
#    GET  /logs/<id>                - View single log
#    GET  /health                   - Health check
# =============================================================

import json
import logging
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
from flask import Flask, request, jsonify
from sap_client import SAPClient
from db import setup_tables, log_operation, save_pulled_data
from config import SAP, PG, API

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("custom_api.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("CustomAPI")

app = Flask(__name__)
sap = SAPClient()


# =============================================================
#  GET / - Homepage (browser friendly)
# =============================================================
@app.route("/", methods=["GET"])
def home():
    """Homepage - interactive UI for testing pull & push."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Custom SAP Data API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; display: flex; height: 100vh; overflow: hidden; }

            /* Sidebar */
            .sidebar { width: 240px; background: #13151e; border-right: 1px solid #1e2130; padding: 24px 0; display: flex; flex-direction: column; flex-shrink: 0; }
            .logo { padding: 0 20px 24px; border-bottom: 1px solid #1e2130; margin-bottom: 16px; }
            .logo h1 { color: #4fc3f7; font-size: 1.1rem; font-weight: 700; }
            .logo p { color: #555; font-size: 0.75rem; margin-top: 2px; }
            .status-pill { display: inline-block; background: #1b5e20; color: #69f0ae; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; margin-top: 6px; }
            .nav-section { padding: 8px 20px 4px; color: #444; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }
            .nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 20px; cursor: pointer; color: #888; font-size: 0.85rem; border-left: 3px solid transparent; transition: all 0.15s; }
            .nav-item:hover { color: #e0e0e0; background: #1a1d27; }
            .nav-item.active { color: #4fc3f7; background: #0d1929; border-left-color: #4fc3f7; }
            .method-badge { font-size: 0.6rem; font-weight: 700; padding: 2px 6px; border-radius: 3px; }
            .get-b { background: #0d47a1; color: #90caf9; }
            .post-b { background: #4a148c; color: #ce93d8; }

            /* Main */
            .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
            .topbar { padding: 16px 28px; background: #13151e; border-bottom: 1px solid #1e2130; display: flex; align-items: center; gap: 12px; }
            .topbar h2 { font-size: 1rem; color: #e0e0e0; }
            .topbar span { color: #555; font-size: 0.85rem; }

            /* Content panels */
            .content { flex: 1; display: flex; overflow: hidden; }
            .panel { padding: 24px 28px; overflow-y: auto; }
            .form-panel { width: 420px; border-right: 1px solid #1e2130; flex-shrink: 0; }
            .result-panel { flex: 1; background: #0b0d14; }

            .form-group { margin-bottom: 18px; }
            label { display: block; font-size: 0.8rem; color: #888; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
            input, select, textarea { width: 100%; background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 6px; padding: 10px 12px; color: #e0e0e0; font-size: 0.875rem; font-family: inherit; outline: none; transition: border-color 0.15s; }
            input:focus, select:focus, textarea:focus { border-color: #4fc3f7; }
            textarea { font-family: 'Consolas', monospace; font-size: 0.8rem; resize: vertical; min-height: 120px; }
            select option { background: #1a1d27; }
            .row { display: flex; gap: 12px; }
            .row .form-group { flex: 1; }

            .btn { width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.15s; margin-top: 4px; }
            .btn-pull { background: #1565c0; color: #e3f2fd; }
            .btn-pull:hover { background: #1976d2; }
            .btn-push { background: #6a1b9a; color: #f3e5f5; }
            .btn-push:hover { background: #7b1fa2; }
            .btn:disabled { opacity: 0.5; cursor: not-allowed; }

            /* Result */
            .result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
            .result-header h3 { color: #888; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }
            .result-status { padding: 3px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
            .s-success { background: #1b5e20; color: #69f0ae; }
            .s-error   { background: #7f0000; color: #ef9a9a; }
            .s-loading { background: #1a237e; color: #90caf9; }
            pre { background: #13151e; border: 1px solid #1e2130; border-radius: 6px; padding: 16px; font-family: 'Consolas', monospace; font-size: 0.8rem; color: #a5d6a7; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; max-height: 100%; }
            .count-badge { background: #1e2130; border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; color: #4fc3f7; }

            /* Quick links */
            .quick-link { display: block; padding: 10px 14px; background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 6px; margin-bottom: 8px; color: #90caf9; text-decoration: none; font-size: 0.85rem; font-family: monospace; transition: all 0.15s; }
            .quick-link:hover { border-color: #4fc3f7; background: #1e2235; }
        </style>
    </head>
    <body>
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="logo">
                <h1>SAP Data API</h1>
                <p>Custom Universal API</p>
                <span class="status-pill">RUNNING</span>
            </div>
            <div class="nav-section">Data Operations</div>
            <div class="nav-item active" onclick="showTab('pull')">
                <span class="method-badge post-b">POST</span> Pull Data
            </div>
            <div class="nav-item" onclick="showTab('push')">
                <span class="method-badge post-b">POST</span> Push Data
            </div>
            <div class="nav-section">Discovery</div>
            <div class="nav-item" onclick="window.open('/services','_blank')">
                <span class="method-badge get-b">GET</span> Services
            </div>
            <div class="nav-item" onclick="showTab('entities')">
                <span class="method-badge get-b">GET</span> Entities
            </div>
            <div class="nav-section">Monitoring</div>
            <div class="nav-item" onclick="window.open('/logs','_blank')">
                <span class="method-badge get-b">GET</span> Operation Logs
            </div>
            <div class="nav-item" onclick="window.open('/health','_blank')">
                <span class="method-badge get-b">GET</span> Health Check
            </div>
        </div>

        <!-- Main -->
        <div class="main">
            <div class="topbar">
                <h2 id="tab-title">Pull Data from SAP</h2>
                <span id="tab-desc">Read records from any SAP OData service</span>
            </div>

            <div class="content">
                <!-- PULL FORM -->
                <div class="form-panel panel" id="tab-pull">
                    <div class="form-group">
                        <label>Service Path</label>
                        <input id="pull-service" value="/sap/opu/odata/sap/API_SALES_ORDER_SRV" placeholder="/sap/opu/odata/sap/...">
                    </div>
                    <div class="form-group">
                        <label>Entity Name</label>
                        <select id="pull-entity" style="margin-bottom:6px">
                            <option value="A_SalesOrder">A_SalesOrder</option>
                            <option value="A_SalesOrderItem">A_SalesOrderItem</option>
                            <option value="A_BusinessPartner">A_BusinessPartner</option>
                            <option value="A_Product">A_Product</option>
                            <option value="A_PurchaseOrder">A_PurchaseOrder</option>
                        </select>
                        <input id="pull-entity-custom" placeholder="Or type custom entity name...">
                    </div>
                    <div class="row">
                        <div class="form-group">
                            <label>Max Records</label>
                            <input id="pull-top" type="number" value="10" min="1" max="5000">
                        </div>
                        <div class="form-group">
                            <label>Save to DB?</label>
                            <select id="pull-save">
                                <option value="true">Yes - Save to sap_data</option>
                                <option value="false">No - Return only</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Filter (optional)</label>
                        <input id="pull-filter" placeholder="e.g. SalesOrderType eq 'OR'">
                    </div>
                    <div class="form-group">
                        <label>Called By</label>
                        <input id="pull-by" value="harish">
                    </div>
                    <button class="btn btn-pull" onclick="doPull()" id="pull-btn">Pull Data from SAP</button>
                </div>

                <!-- PUSH FORM -->
                <div class="form-panel panel" id="tab-push" style="display:none">
                    <div class="form-group">
                        <label>Operation</label>
                        <select id="push-op" onchange="togglePushFields()">
                            <option value="update">Update Existing Record</option>
                            <option value="create">Create New Record</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Service Path</label>
                        <input id="push-service" value="/sap/opu/odata/sap/API_SALES_ORDER_SRV">
                    </div>
                    <div class="form-group" id="push-entity-group">
                        <label>Entity with Key (for Update)</label>
                        <input id="push-entity-key" value="A_SalesOrder('2')" placeholder="A_SalesOrder('2')">
                    </div>
                    <div class="form-group" id="push-entity-name-group" style="display:none">
                        <label>Entity Name (for Create)</label>
                        <input id="push-entity-name" value="A_SalesOrder" placeholder="A_SalesOrder">
                    </div>
                    <div class="form-group">
                        <label>Record ID (mata_id)</label>
                        <input id="push-mataid" value="2" placeholder="Unique SAP key">
                    </div>
                    <div class="form-group">
                        <label>Payload (JSON)</label>
                        <textarea id="push-payload">{
  "PurchaseOrderByCustomer": "MY_UPDATE_001"
}</textarea>
                    </div>
                    <div class="form-group">
                        <label>Called By</label>
                        <input id="push-by" value="harish">
                    </div>
                    <button class="btn btn-push" onclick="doPush()" id="push-btn">Push to SAP</button>
                </div>

                <!-- ENTITIES FORM -->
                <div class="form-panel panel" id="tab-entities" style="display:none">
                    <div class="form-group">
                        <label>Service Name</label>
                        <input id="ent-service" value="ZAPI_SALES_ORDER_SRV" placeholder="e.g. ZAPI_SALES_ORDER_SRV">
                    </div>
                    <button class="btn btn-pull" onclick="doEntities()">Get Entities</button>
                    <div style="margin-top:24px">
                        <label>Quick Links</label>
                        <a class="quick-link" href="/services" target="_blank">/services — All SAP services</a>
                        <a class="quick-link" href="/logs" target="_blank">/logs — Operation history</a>
                        <a class="quick-link" href="/health" target="_blank">/health — Health check</a>
                    </div>
                </div>

                <!-- RESULT PANEL -->
                <div class="result-panel panel">
                    <div class="result-header">
                        <h3>Response</h3>
                        <span class="result-status s-loading" id="result-status">READY</span>
                        <span class="count-badge" id="result-count" style="display:none"></span>
                    </div>
                    <pre id="result-box">// Results will appear here after you send a request</pre>
                </div>
            </div>
        </div>

        <script>
            function showTab(tab) {
                ['pull','push','entities'].forEach(t => {
                    document.getElementById('tab-' + t).style.display = 'none';
                });
                document.getElementById('tab-' + tab).style.display = '';
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                event.target.closest('.nav-item').classList.add('active');

                const titles = {
                    pull: ['Pull Data from SAP', 'Read records from any SAP OData service'],
                    push: ['Push Data to SAP', 'Create or update records in SAP'],
                    entities: ['Discover Entities', 'List all entity sets in a service'],
                };
                document.getElementById('tab-title').textContent = titles[tab][0];
                document.getElementById('tab-desc').textContent = titles[tab][1];
            }

            function togglePushFields() {
                const op = document.getElementById('push-op').value;
                document.getElementById('push-entity-group').style.display = op === 'update' ? '' : 'none';
                document.getElementById('push-entity-name-group').style.display = op === 'create' ? '' : 'none';
            }

            function setResult(data, status) {
                const el = document.getElementById('result-box');
                const st = document.getElementById('result-status');
                const cn = document.getElementById('result-count');

                el.textContent = JSON.stringify(data, null, 2);
                st.textContent = status;
                st.className = 'result-status ' + (
                    status === 'SUCCESS' ? 's-success' :
                    status === 'LOADING...' ? 's-loading' : 's-error'
                );

                if (data && data.records_count !== undefined) {
                    cn.textContent = data.records_count + ' records';
                    cn.style.display = '';
                } else { cn.style.display = 'none'; }
            }

            async function doPull() {
                const entity = document.getElementById('pull-entity-custom').value ||
                               document.getElementById('pull-entity').value;
                const btn = document.getElementById('pull-btn');
                btn.disabled = true;
                btn.textContent = 'Pulling...';
                setResult({message: 'Sending request to SAP...'}, 'LOADING...');

                try {
                    const body = {
                        service_path: document.getElementById('pull-service').value,
                        entity_name: entity,
                        top: parseInt(document.getElementById('pull-top').value) || 10,
                        save_to_db: document.getElementById('pull-save').value === 'true',
                        called_by: document.getElementById('pull-by').value || 'browser_user',
                    };
                    const filter = document.getElementById('pull-filter').value;
                    if (filter) body.filters = filter;

                    const r = await fetch('/pull', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(body)
                    });
                    const data = await r.json();
                    setResult(data, data.status || (r.ok ? 'SUCCESS' : 'ERROR'));
                } catch(e) {
                    setResult({error: e.message}, 'ERROR');
                } finally {
                    btn.disabled = false;
                    btn.textContent = 'Pull Data from SAP';
                }
            }

            async function doPush() {
                const op = document.getElementById('push-op').value;
                const btn = document.getElementById('push-btn');
                btn.disabled = true;
                btn.textContent = 'Pushing...';
                setResult({message: 'Sending request to SAP...'}, 'LOADING...');

                let payload;
                try { payload = JSON.parse(document.getElementById('push-payload').value); }
                catch(e) { setResult({error: 'Invalid JSON in payload: ' + e.message}, 'ERROR'); btn.disabled=false; btn.textContent='Push to SAP'; return; }

                try {
                    let body, url;
                    if (op === 'update') {
                        url = '/push/update';
                        body = {
                            service_path: document.getElementById('push-service').value,
                            entity_with_key: document.getElementById('push-entity-key').value,
                            mata_id: document.getElementById('push-mataid').value,
                            payload,
                            called_by: document.getElementById('push-by').value || 'browser_user',
                        };
                    } else {
                        url = '/push';
                        body = {
                            service_path: document.getElementById('push-service').value,
                            entity_name: document.getElementById('push-entity-name').value,
                            mata_id: document.getElementById('push-mataid').value,
                            payload,
                            called_by: document.getElementById('push-by').value || 'browser_user',
                        };
                    }

                    const r = await fetch(url, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(body)
                    });
                    const data = await r.json();
                    setResult(data, data.status || (r.ok ? 'SUCCESS' : 'ERROR'));
                } catch(e) {
                    setResult({error: e.message}, 'ERROR');
                } finally {
                    btn.disabled = false;
                    btn.textContent = 'Push to SAP';
                }
            }

            async function doEntities() {
                const name = document.getElementById('ent-service').value;
                setResult({message: 'Fetching entities...'}, 'LOADING...');
                try {
                    const r = await fetch('/services/' + name + '/entities');
                    const data = await r.json();
                    setResult(data, r.ok ? 'SUCCESS' : 'ERROR');
                } catch(e) {
                    setResult({error: e.message}, 'ERROR');
                }
            }
        </script>
    </body>
    </html>
    """

# =============================================================
#  GET /services - List all available SAP services
# =============================================================
@app.route("/services", methods=["GET"])
def list_services():
    """List all available OData services on SAP."""
    search = request.args.get("search", "").upper()

    try:
        services = sap.discover_services()

        if search:
            services = [s for s in services if search in s["name"].upper()]

        return jsonify({
            "total": len(services),
            "services": services,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================
#  GET /services/<name>/entities - List entities in a service
# =============================================================
@app.route("/services/<service_name>/entities", methods=["GET"])
def list_entities(service_name):
    """List all entity sets (tables) in a service."""
    try:
        # Find the service URL
        services = sap.discover_services()
        svc = None
        for s in services:
            if s["name"].upper() == service_name.upper():
                svc = s
                break
            if service_name.upper() in s["name"].upper():
                svc = s
                break

        if not svc:
            return jsonify({"error": f"Service '{service_name}' not found"}), 404

        entities = sap.discover_entities(svc["url"])

        return jsonify({
            "service": svc["name"],
            "service_url": svc["url"],
            "total": len(entities),
            "entities": entities,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================
#  POST /pull - Pull data from ANY SAP service
# =============================================================
@app.route("/pull", methods=["POST"])
def pull_data():
    """
    Pull data from any SAP service.

    Request JSON:
    {
        "service_path": "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
        "entity_name": "A_SalesOrder",
        "filters": "SalesOrderType eq 'OR'",    (optional)
        "top": 100,                              (optional, default 1000)
        "select": "SalesOrder,SalesOrderType",   (optional)
        "save_to_db": true,                      (optional, default true)
        "called_by": "ai_team"                   (optional)
    }

    Response:
    {
        "log_id": 1,
        "status": "SUCCESS",
        "records_count": 50,
        "data": [ {...}, {...}, ... ]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload"}), 400

    service_path = data.get("service_path")
    entity_name = data.get("entity_name")

    if not service_path:
        return jsonify({"error": "Missing 'service_path'"}), 400
    if not entity_name:
        return jsonify({"error": "Missing 'entity_name'"}), 400

    filters = data.get("filters")
    top = data.get("top", 1000)
    select = data.get("select")
    save_to_db = data.get("save_to_db", True)
    called_by = data.get("called_by", "api_user")
    max_records = data.get("max_records", 10000)

    service_name = service_path.rstrip("/").split("/")[-1]
    log.info(f"PULL: {service_name}/{entity_name} by {called_by}")

    try:
        records = sap.pull(
            service_path, entity_name,
            filters=filters, top=top, select=select,
            max_records=max_records
        )

        # Save to database if requested
        saved = 0
        if save_to_db and records:
            saved = save_pulled_data(service_name, entity_name, records)

        # Log the operation
        log_id = log_operation(
            operation="PULL",
            service_name=service_name,
            entity_name=entity_name,
            records_count=len(records),
            status="SUCCESS",
            status_code=200,
            called_by=called_by,
            request_payload={"filters": filters, "top": top, "select": select},
        )

        return jsonify({
            "log_id": log_id,
            "status": "SUCCESS",
            "records_count": len(records),
            "saved_to_db": saved,
            "data": records,
        })

    except Exception as e:
        log_id = log_operation(
            operation="PULL",
            service_name=service_name,
            entity_name=entity_name,
            status="ERROR",
            error_message=str(e),
            called_by=called_by,
        )
        return jsonify({
            "log_id": log_id,
            "status": "ERROR",
            "error": str(e),
        }), 500


# =============================================================
#  POST /push - Create new record in ANY SAP service
# =============================================================
@app.route("/push", methods=["POST"])
def push_create():
    """
    Push (create) a new record in any SAP service.

    Request JSON:
    {
        "service_path": "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
        "entity_name": "A_SalesOrder",
        "mata_id": "ORDER001",
        "payload": {
            "SalesOrderType": "OR",
            "SalesOrganization": "1710"
        },
        "called_by": "ai_team"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload"}), 400

    service_path = data.get("service_path")
    entity_name = data.get("entity_name")
    payload = data.get("payload")

    if not service_path:
        return jsonify({"error": "Missing 'service_path'"}), 400
    if not entity_name:
        return jsonify({"error": "Missing 'entity_name'"}), 400
    if not payload:
        return jsonify({"error": "Missing 'payload'"}), 400

    mata_id = data.get("mata_id", "")
    called_by = data.get("called_by", "api_user")
    service_name = service_path.rstrip("/").split("/")[-1]

    log.info(f"PUSH CREATE: {service_name}/{entity_name} by {called_by}")

    result = sap.push_create(service_path, entity_name, payload)

    log_id = log_operation(
        operation="PUSH_CREATE",
        service_name=service_name,
        entity_name=entity_name,
        mata_id=mata_id,
        request_payload=payload,
        response_data=result["data"],
        status=result["status"],
        status_code=result["status_code"],
        error_message=result["error"],
        called_by=called_by,
    )

    return jsonify({
        "log_id": log_id,
        "status": result["status"],
        "status_code": result["status_code"],
        "message": f"Create {'successful' if result['status'] == 'SUCCESS' else 'failed'}",
        "data": result["data"],
        "error": result["error"],
    }), 200 if result["status"] == "SUCCESS" else 500


# =============================================================
#  POST /push/update - Update record in ANY SAP service
# =============================================================
@app.route("/push/update", methods=["POST"])
def push_update():
    """
    Update an existing record in any SAP service.

    Request JSON:
    {
        "service_path": "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
        "entity_with_key": "A_SalesOrder('2')",
        "mata_id": "2",
        "payload": {
            "PurchaseOrderByCustomer": "UPDATED_VALUE"
        },
        "called_by": "ai_team"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload"}), 400

    service_path = data.get("service_path")
    entity_with_key = data.get("entity_with_key")
    payload = data.get("payload")

    if not service_path:
        return jsonify({"error": "Missing 'service_path'"}), 400
    if not entity_with_key:
        return jsonify({"error": "Missing 'entity_with_key'"}), 400
    if not payload:
        return jsonify({"error": "Missing 'payload'"}), 400

    mata_id = data.get("mata_id", "")
    called_by = data.get("called_by", "api_user")
    service_name = service_path.rstrip("/").split("/")[-1]
    entity_name = entity_with_key.split("(")[0] if "(" in entity_with_key else entity_with_key

    log.info(f"PUSH UPDATE: {service_name}/{entity_with_key} by {called_by}")

    result = sap.push_update(service_path, entity_with_key, payload)

    log_id = log_operation(
        operation="PUSH_UPDATE",
        service_name=service_name,
        entity_name=entity_name,
        mata_id=mata_id,
        request_payload=payload,
        response_data=result["data"],
        status=result["status"],
        status_code=result["status_code"],
        error_message=result["error"],
        called_by=called_by,
    )

    return jsonify({
        "log_id": log_id,
        "status": result["status"],
        "status_code": result["status_code"],
        "message": f"Update {'successful' if result['status'] == 'SUCCESS' else 'failed'}",
        "data": result["data"],
        "error": result["error"],
    }), 200 if result["status"] == "SUCCESS" else 500


# =============================================================
#  GET /logs - View all operation logs
# =============================================================
@app.route("/logs", methods=["GET"])
def get_logs():
    """
    View all API operations with status.

    Query params:
        ?operation=PULL          - filter by operation type
        ?status=SUCCESS          - filter by status
        ?service=API_SALES_ORDER - filter by service
        ?called_by=ai_team       - filter by caller
        ?limit=50                - limit results
    """
    schema = PG["schema"]
    operation = request.args.get("operation")
    status = request.args.get("status")
    service = request.args.get("service")
    called_by = request.args.get("called_by")
    limit = request.args.get("limit", 100, type=int)

    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = f"SELECT * FROM {schema}.api_log WHERE 1=1"
            params = []

            if operation:
                query += " AND operation = %s"
                params.append(operation.upper())
            if status:
                query += " AND status = %s"
                params.append(status.upper())
            if service:
                query += " AND service_name ILIKE %s"
                params.append(f"%{service}%")
            if called_by:
                query += " AND called_by = %s"
                params.append(called_by)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

            for row in rows:
                for key, val in row.items():
                    if isinstance(val, datetime):
                        row[key] = val.isoformat()

            # Summary
            cur.execute(f"""
                SELECT operation, status, COUNT(*) as count
                FROM {schema}.api_log
                GROUP BY operation, status
                ORDER BY operation, status
            """)
            summary = [dict(r) for r in cur.fetchall()]

            return jsonify({
                "total": len(rows),
                "summary": summary,
                "logs": rows,
            })
    finally:
        conn.close()


# =============================================================
#  GET /logs/<id> - View single log
# =============================================================
@app.route("/logs/<int:log_id>", methods=["GET"])
def get_log_by_id(log_id):
    """View a single operation log."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {schema}.api_log WHERE id = %s", (log_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": f"Log ID {log_id} not found"}), 404
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
        "service": "Custom SAP Data API",
        "sap_server": f"{SAP['host']}:{SAP['port']}",
        "db_schema": PG["schema"],
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "GET  /services": "List all SAP services",
            "GET  /services/<name>/entities": "List entities in a service",
            "POST /pull": "Pull data from SAP",
            "POST /push": "Create new record in SAP",
            "POST /push/update": "Update record in SAP",
            "GET  /logs": "View all operation logs",
            "GET  /logs/<id>": "View single operation log",
            "GET  /health": "This endpoint",
        }
    })


# =============================================================
#  START
# =============================================================
if __name__ == "__main__":
    log.info("Setting up database tables...")
    setup_tables()

    log.info("=" * 60)
    log.info("  Custom SAP Data API")
    log.info(f"  SAP Server: {SAP['host']}:{SAP['port']}")
    log.info(f"  DB Schema:  {PG['schema']}")
    log.info(f"  API URL:    http://localhost:{API['port']}")
    log.info("=" * 60)
    log.info("Endpoints:")
    log.info("  GET  /services              - List SAP services")
    log.info("  GET  /services/<n>/entities - List entities")
    log.info("  POST /pull                  - Pull data from SAP")
    log.info("  POST /push                  - Create record in SAP")
    log.info("  POST /push/update           - Update record in SAP")
    log.info("  GET  /logs                  - Operation logs")
    log.info("  GET  /health                - Health check")
    log.info("=" * 60)

    app.run(host=API["host"], port=API["port"], debug=True)
