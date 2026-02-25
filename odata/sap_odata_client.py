#!/usr/bin/env python3
# =============================================================
#  sap_odata_client.py - SAP OData REST API Client
#
#  Connects to SAP via HTTP/HTTPS OData services.
#  Tries multiple ports and protocols automatically.
#
#  REQUIRES: OData services to be enabled on SAP server
# =============================================================

import sys
import logging
import requests
from requests.auth import HTTPBasicAuth
from config import SAP

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("odata.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("OData")


class SAPODataClient:
    """
    SAP OData REST API Client.

    Flow:
        1. _find_active_url() tries every port/protocol combo
        2. pull() fetches data as JSON via GET requests
        3. push_update() sends PATCH requests with CSRF token

    Example:
        client = SAPODataClient()
        data = client.pull("/sap/opu/odata/sap/API_PRODUCT_SRV", "A_Product")
    """

    def __init__(self):
        self.base_host = SAP["host"]
        self.base_ip   = SAP["ip"]
        self.ports     = SAP["ports"]
        self.timeout   = SAP["timeout"]

        # Session with auth and headers
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(SAP["username"], SAP["password"])
        self.session.headers.update({
            "Accept":       "application/json",
            "Content-Type": "application/json",
            "sap-client":   SAP["client"],
        })
        self.session.verify = False  # Skip SSL cert validation

        self.active_url = None

    # ---------------------------------------------------------
    #  PORT DISCOVERY
    # ---------------------------------------------------------
    def _find_active_url(self, service_path):
        """
        Tries every combination of host/protocol/port to find
        one that responds. SAP OData typically runs on:
          - 8000/8040 (HTTP)
          - 443/44340 (HTTPS)
          - 3240/3340 (Dispatcher/RFC - less common for OData)
        """
        protocols = ["http", "https"]
        hosts     = [self.base_host, self.base_ip]

        for host in hosts:
            for proto in protocols:
                for port in self.ports:
                    url = f"{proto}://{host}:{port}{service_path}"
                    log.info(f"Testing: {url}")
                    try:
                        resp = self.session.get(url, timeout=5)
                        if resp.status_code < 500:
                            log.info(f"CONNECTED! {proto}://{host}:{port} (HTTP {resp.status_code})")
                            self.active_url = f"{proto}://{host}:{port}"
                            return self.active_url
                    except requests.exceptions.ConnectTimeout:
                        log.debug(f"  Timeout: {port}")
                    except requests.exceptions.ConnectionError:
                        log.debug(f"  Refused: {port}")
                    except Exception as e:
                        log.debug(f"  Error: {e}")

        raise ConnectionError(
            f"Could not connect to SAP OData at {self.base_host} on any port.\n"
            f"Ports tried: {self.ports}\n"
            f"Possible fixes:\n"
            f"  1. Ask SAP Basis team to enable OData (ICF service activation)\n"
            f"  2. Check if a VPN is required\n"
            f"  3. Use the GUI method instead: python pull_sap/sap_pull.py MARA"
        )

    # ---------------------------------------------------------
    #  CSRF TOKEN (needed for write operations)
    # ---------------------------------------------------------
    def _get_csrf_token(self, service_path):
        if not self.active_url:
            self._find_active_url(service_path)

        url  = f"{self.active_url}{service_path}"
        resp = self.session.get(url, headers={"x-csrf-token": "Fetch"}, timeout=self.timeout)
        token = resp.headers.get("x-csrf-token")
        if not token:
            raise RuntimeError("CSRF token fetch failed - check SAP credentials.")
        return token

    # ---------------------------------------------------------
    #  PULL (GET - read data)
    # ---------------------------------------------------------
    def pull(self, service_path, entity, params=None, max_records=10000):
        """
        Pulls data from an OData entity set.

        Args:
            service_path: e.g. "/sap/opu/odata/sap/API_PRODUCT_SRV"
            entity:       e.g. "A_Product"
            params:       additional OData query params ($filter, $select, etc.)
            max_records:  safety limit

        Returns:
            List of dicts (one per SAP record)

        OData pagination:
            SAP returns max ~1000 records per request.
            If there are more, the response includes a "__next" URL.
            We follow these links automatically.
        """
        if not self.active_url:
            self._find_active_url(service_path)

        url = f"{self.active_url}{service_path}/{entity}"
        all_records = []
        query = {"$format": "json", "$top": 1000}
        if params:
            query.update(params)

        page = 1
        while url and len(all_records) < max_records:
            log.info(f"Pulling {entity} (page {page}): {url}")
            try:
                resp = self.session.get(url, params=query, timeout=self.timeout)
                resp.raise_for_status()

                data    = resp.json().get("d", {})
                records = data.get("results", [])
                all_records.extend(records)
                log.info(f"  Page {page}: {len(records)} records (total: {len(all_records)})")

                # Follow pagination link
                url   = data.get("__next")
                query = {}  # __next URL already has params
                page += 1

            except Exception as e:
                log.error(f"Pull failed: {e}")
                raise

        return all_records

    # ---------------------------------------------------------
    #  PUSH (PATCH - update data)
    # ---------------------------------------------------------
    def push_update(self, service_path, entity_with_key, payload):
        """
        Updates a single record in SAP via PATCH.

        Args:
            service_path:    e.g. "/sap/opu/odata/sap/API_PRODUCT_SRV"
            entity_with_key: e.g. "A_Product('MAT001')"
            payload:         dict of fields to update

        Returns:
            HTTP status code (200/204 = success)
        """
        if not self.active_url:
            self._find_active_url(service_path)

        token = self._get_csrf_token(service_path)
        url   = f"{self.active_url}{service_path}/{entity_with_key}"

        resp = self.session.patch(
            url, json=payload,
            headers={"x-csrf-token": token},
            params={"$format": "json"},
            timeout=self.timeout
        )
        resp.raise_for_status()
        log.info(f"Updated {entity_with_key}: HTTP {resp.status_code}")
        return resp.status_code


# =============================================================
#  QUICK TEST - Run this file directly to test connectivity
# =============================================================
if __name__ == "__main__":
    from config import SERVICES

    client = SAPODataClient()
    service = SERVICES.get("material", "/sap/opu/odata/sap/API_PRODUCT_SRV")

    print("=" * 55)
    print("Testing SAP OData connectivity...")
    print(f"Host: {SAP['host']}")
    print(f"Ports: {SAP['ports']}")
    print("=" * 55)

    try:
        url = client._find_active_url(service)
        print(f"\nSUCCESS! Active URL: {url}")
        print("OData is reachable. You can now pull data.")
    except ConnectionError as e:
        print(f"\nFAILED: {e}")
        print("\nOData is NOT reachable. Use GUI method instead:")
        print("  python pull_sap/sap_pull.py MARA")
