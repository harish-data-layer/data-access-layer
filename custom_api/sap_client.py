#!/usr/bin/env python3
# =============================================================
#  custom_api/sap_client.py
#
#  Universal SAP OData client - handles ANY service
#  Both PULL (GET) and PUSH (POST/PATCH) operations
# =============================================================

import json
import logging
import requests
from requests.auth import HTTPBasicAuth
from config import SAP

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger("SAPClient")


class SAPClient:
    """Universal SAP OData client for any service."""

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

    # ---------------------------------------------------------
    #  DISCOVER - List all services or entities
    # ---------------------------------------------------------
    def discover_services(self):
        """Get all available OData services from SAP catalog."""
        url = f"{self.base_url}/sap/opu/odata/IWFND/CATALOGSERVICE;v=2/ServiceCollection"
        all_services = []
        params = {"$format": "json", "$top": 500}

        resp = self.session.get(url, params=params, timeout=SAP["timeout"])
        resp.raise_for_status()
        results = resp.json().get("d", {}).get("results", [])

        for svc in results:
            title = svc.get("Title", "")
            tech_name = svc.get("TechnicalServiceName", title)
            svc_url = svc.get("ServiceUrl", "")
            if tech_name and svc_url:
                all_services.append({
                    "name": tech_name,
                    "url": svc_url,
                    "title": title,
                    "version": svc.get("TechnicalServiceVersion", ""),
                })

        return all_services

    def discover_entities(self, service_path):
        """Get all entity sets for a service."""
        if service_path.startswith("http"):
            url = f"{service_path}/$metadata"
            meta_url = service_path
        else:
            url = f"{self.base_url}{service_path}/$metadata"
            meta_url = f"{self.base_url}{service_path}"

        # Try JSON first to get entity set names
        try:
            resp = self.session.get(meta_url, params={"$format": "json"}, timeout=SAP["timeout"])
            if resp.status_code == 200:
                data = resp.json().get("d", {})
                # EntitySets are listed in the service document
                entity_sets = data.get("EntitySets", [])
                if entity_sets:
                    return entity_sets
        except Exception:
            pass

        # Fallback: parse $metadata XML
        try:
            resp = self.session.get(url, timeout=SAP["timeout"])
            if resp.status_code == 200:
                import re
                entities = re.findall(r'EntitySet\s+Name="([^"]+)"', resp.text)
                return entities
        except Exception:
            pass

        return []

    # ---------------------------------------------------------
    #  PULL - Read data from SAP
    # ---------------------------------------------------------
    def pull(self, service_path, entity_name, filters=None, top=1000, skip=0, select=None, max_records=10000):
        """
        Pull data from ANY SAP OData service.

        Args:
            service_path: e.g. "/sap/opu/odata/sap/API_SALES_ORDER_SRV"
            entity_name:  e.g. "A_SalesOrder"
            filters:      OData $filter string (optional)
            top:          records per page (default 1000)
            skip:         skip first N records
            select:       comma-separated fields to return
            max_records:  max total records to pull

        Returns:
            list of records (dicts)
        """
        if service_path.startswith("http"):
            entity_url = f"{service_path}/{entity_name}"
        else:
            entity_url = f"{self.base_url}{service_path}/{entity_name}"

        all_records = []
        params = {"$format": "json", "$top": top}

        if filters:
            params["$filter"] = filters
        if skip:
            params["$skip"] = skip
        if select:
            params["$select"] = select

        url = entity_url
        page = 1

        while url and len(all_records) < max_records:
            try:
                resp = self.session.get(url, params=params, timeout=SAP["timeout"])

                if resp.status_code in (404, 403) or resp.status_code >= 500:
                    log.warning(f"Entity {entity_name}: HTTP {resp.status_code}")
                    break

                resp.raise_for_status()
                data = resp.json().get("d", {})
                results = data.get("results", [])

                if not results and isinstance(data, list):
                    results = data

                # Clean records - remove OData metadata
                for rec in results:
                    clean = {}
                    for k, v in rec.items():
                        if k.startswith("__") or isinstance(v, (dict, list)):
                            continue
                        clean[k] = v
                    all_records.append(clean)

                url = data.get("__next") if isinstance(data, dict) else None
                params = {}
                page += 1

            except requests.exceptions.Timeout:
                log.warning(f"Timeout on page {page}")
                break
            except Exception as e:
                log.error(f"Pull error: {e}")
                break

        return all_records

    # ---------------------------------------------------------
    #  PUSH CREATE - Create new record in SAP
    # ---------------------------------------------------------
    def push_create(self, service_path, entity_name, payload):
        """
        Create a new record in SAP via POST.

        Returns: dict with status, status_code, data, error
        """
        try:
            # Get CSRF token
            token_url = f"{self.base_url}{service_path}" if not service_path.startswith("http") else service_path
            resp = self.session.get(token_url, headers={"x-csrf-token": "Fetch"}, timeout=SAP["timeout"])
            token = resp.headers.get("x-csrf-token", "")

            # POST
            url = f"{self.base_url}{service_path}/{entity_name}" if not service_path.startswith("http") else f"{service_path}/{entity_name}"
            resp = self.session.post(
                url,
                json=payload,
                headers={"x-csrf-token": token},
                timeout=SAP["timeout"]
            )

            result = {
                "status": "SUCCESS" if resp.status_code in (200, 201, 204) else "FAILED",
                "status_code": resp.status_code,
                "data": None,
                "error": None,
            }

            if resp.status_code in (200, 201):
                try:
                    result["data"] = resp.json().get("d", {})
                except Exception:
                    result["data"] = {"message": "Created"}
            elif resp.status_code == 204:
                result["data"] = {"message": "Created successfully"}
            else:
                result["error"] = resp.text[:500]

            return result

        except Exception as e:
            return {"status": "ERROR", "status_code": 0, "data": None, "error": str(e)}

    # ---------------------------------------------------------
    #  PUSH UPDATE - Update existing record in SAP
    # ---------------------------------------------------------
    def push_update(self, service_path, entity_with_key, payload):
        """
        Update existing record in SAP via PATCH.

        Args:
            entity_with_key: e.g. "A_SalesOrder('2')"

        Returns: dict with status, status_code, data, error
        """
        try:
            token_url = f"{self.base_url}{service_path}" if not service_path.startswith("http") else service_path
            resp = self.session.get(token_url, headers={"x-csrf-token": "Fetch"}, timeout=SAP["timeout"])
            token = resp.headers.get("x-csrf-token", "")

            url = f"{self.base_url}{service_path}/{entity_with_key}" if not service_path.startswith("http") else f"{service_path}/{entity_with_key}"
            resp = self.session.patch(
                url,
                json=payload,
                headers={"x-csrf-token": token, "If-Match": "*"},
                timeout=SAP["timeout"]
            )

            result = {
                "status": "SUCCESS" if resp.status_code in (200, 204) else "FAILED",
                "status_code": resp.status_code,
                "data": None,
                "error": None,
            }

            if resp.status_code == 200:
                try:
                    result["data"] = resp.json().get("d", {})
                except Exception:
                    result["data"] = {"message": "Updated"}
            elif resp.status_code == 204:
                result["data"] = {"message": "Updated successfully"}
            else:
                result["error"] = resp.text[:500]

            return result

        except Exception as e:
            return {"status": "ERROR", "status_code": 0, "data": None, "error": str(e)}
