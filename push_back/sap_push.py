#!/usr/bin/env python3
# =============================================================
#  push_back/sap_push.py
#
#  Pushes data back to SAP via OData API (POST/PATCH)
#  and logs status in sap_sap.push_sap table
# =============================================================

import json
import logging
import requests
import psycopg2
from datetime import datetime
from requests.auth import HTTPBasicAuth
from config import SAP, PG

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("SAPPush")


# =============================================================
#  SAP OData Push Client
# =============================================================
class SAPPushClient:
    """Push data to SAP via OData POST/PATCH requests."""

    def __init__(self):
        self.base_url = f"{SAP['protocol']}://{SAP['host']}:{SAP['port']}"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(SAP["username"], SAP["password"])
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "sap-client": SAP["client"],
        })
        self.session.verify = False

    def _get_csrf_token(self, service_path):
        """Fetch CSRF token (required for SAP write operations)."""
        url = f"{self.base_url}{service_path}"
        resp = self.session.get(
            url,
            headers={"x-csrf-token": "Fetch"},
            timeout=SAP["timeout"]
        )
        token = resp.headers.get("x-csrf-token")
        if not token:
            raise RuntimeError(f"CSRF token fetch failed (HTTP {resp.status_code})")
        return token

    def push_create(self, service_path, entity_name, payload):
        """
        CREATE a new record in SAP (POST request).

        Args:
            service_path: e.g. "/sap/opu/odata/sap/API_SALES_ORDER_SRV"
            entity_name:  e.g. "A_SalesOrder"
            payload:      dict of field values

        Returns:
            dict with status, status_code, response_data, error_message
        """
        try:
            token = self._get_csrf_token(service_path)
            url = f"{self.base_url}{service_path}/{entity_name}"

            log.info(f"POST {url}")
            resp = self.session.post(
                url,
                json=payload,
                headers={"x-csrf-token": token},
                timeout=SAP["timeout"]
            )

            result = {
                "status_code": resp.status_code,
                "status": "SUCCESS" if resp.status_code in (200, 201, 204) else "FAILED",
                "response_data": None,
                "error_message": None,
            }

            if resp.status_code in (200, 201):
                result["response_data"] = resp.json().get("d", {})
            elif resp.status_code == 204:
                result["response_data"] = {"message": "Created successfully (no content)"}
            else:
                result["error_message"] = resp.text[:500]

            return result

        except Exception as e:
            return {
                "status_code": 0,
                "status": "ERROR",
                "response_data": None,
                "error_message": str(e),
            }

    def push_update(self, service_path, entity_with_key, payload):
        """
        UPDATE an existing record in SAP (PATCH request).

        Args:
            service_path:    e.g. "/sap/opu/odata/sap/API_SALES_ORDER_SRV"
            entity_with_key: e.g. "A_SalesOrder('100001')"
            payload:         dict of fields to update

        Returns:
            dict with status, status_code, response_data, error_message
        """
        try:
            token = self._get_csrf_token(service_path)
            url = f"{self.base_url}{service_path}/{entity_with_key}"

            log.info(f"PATCH {url}")
            resp = self.session.patch(
                url,
                json=payload,
                headers={
                    "x-csrf-token": token,
                    "If-Match": "*",
                },
                timeout=SAP["timeout"]
            )

            result = {
                "status_code": resp.status_code,
                "status": "SUCCESS" if resp.status_code in (200, 204) else "FAILED",
                "response_data": None,
                "error_message": None,
            }

            if resp.status_code == 200:
                result["response_data"] = resp.json().get("d", {})
            elif resp.status_code == 204:
                result["response_data"] = {"message": "Updated successfully"}
            else:
                result["error_message"] = resp.text[:500]

            return result

        except Exception as e:
            return {
                "status_code": 0,
                "status": "ERROR",
                "response_data": None,
                "error_message": str(e),
            }


# =============================================================
#  LOG TO push_sap TABLE
# =============================================================
def log_push(service_name, entity_name, mata_id, action, request_payload,
             status, status_code, response_data, error_message, pushed_by="ai_team"):
    """Save push operation record to sap_sap.push_sap table."""
    schema = PG["schema"]
    conn = psycopg2.connect(
        host=PG["host"], port=PG["port"],
        dbname=PG["database"], user=PG["user"], password=PG["password"]
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {schema}.push_sap
                    (service_name, entity_name, mata_id, action,
                     request_payload, response_data,
                     status, status_code, error_message, pushed_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                service_name, entity_name, mata_id, action,
                json.dumps(request_payload, ensure_ascii=False),
                json.dumps(response_data, ensure_ascii=False) if response_data else None,
                status, status_code, error_message, pushed_by
            ))
            push_id = cur.fetchone()[0]
            conn.commit()
            return push_id
    finally:
        conn.close()
