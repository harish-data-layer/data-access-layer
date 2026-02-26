#!/usr/bin/env python3
# =============================================================
#  whole_sap/discover_services.py
#
#  Discovers ALL available OData services on the SAP server
#  by querying the IWFND Catalog Service.
#
#  USAGE:
#    python discover_services.py           <- list all services
#    python discover_services.py --save    <- save to services.json
# =============================================================

import sys
import json
import logging
import requests
from requests.auth import HTTPBasicAuth
from config import SAP, CATALOG_URL, SKIP_SERVICES

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("whole_sap.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("Discover")


def get_base_url():
    """Build the base URL from config."""
    return f"{SAP['protocol']}://{SAP['host']}:{SAP['port']}"


def create_session():
    """Create an authenticated requests session."""
    session = requests.Session()
    session.auth = HTTPBasicAuth(SAP["username"], SAP["password"])
    session.headers.update({
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "sap-client":   SAP["client"],
    })
    session.verify = False
    return session


def discover_services():
    """
    Query the SAP OData Catalog to discover all available services.

    The catalog is at:
      /sap/opu/odata/IWFND/CATALOGSERVICE;v=2/ServiceCollection

    Returns a list of dicts with service info:
      - Title, TechnicalServiceName, ServiceUrl, etc.
    """
    session  = create_session()
    base_url = get_base_url()
    url      = f"{base_url}{CATALOG_URL}/ServiceCollection"

    log.info(f"Discovering services from: {url}")

    all_services = []
    params = {"$format": "json", "$top": 500}

    while url:
        try:
            resp = session.get(url, params=params, timeout=SAP["timeout"])
            resp.raise_for_status()

            data     = resp.json().get("d", {})
            services = data.get("results", [])
            all_services.extend(services)

            log.info(f"  Found {len(services)} services (total: {len(all_services)})")

            url    = data.get("__next")
            params = {}
        except Exception as e:
            log.error(f"Catalog query failed: {e}")
            raise

    # Filter out skipped services and clean up
    filtered = []
    for svc in all_services:
        tech_name = svc.get("TechnicalServiceName", "")
        if tech_name in SKIP_SERVICES:
            log.info(f"  Skipping system service: {tech_name}")
            continue
        filtered.append({
            "title":              svc.get("Title", ""),
            "technical_name":     tech_name,
            "version":            svc.get("TechnicalServiceVersion", ""),
            "service_url":        svc.get("ServiceUrl", ""),
            "description":        svc.get("Description", ""),
            "is_sap_service":     svc.get("IsSapService", False),
        })

    log.info(f"\nTotal usable services: {len(filtered)}")
    return filtered


def discover_entity_sets(service_url):
    """
    For a given OData service URL, discover its entity sets (tables).

    Queries the service metadata ($metadata) or the root document
    to list available entity sets.

    Returns list of entity set names.
    """
    session  = create_session()
    base_url = get_base_url()

    # Build full URL - service_url may be relative or absolute
    if service_url.startswith("http"):
        full_url = service_url
    else:
        # Normalize the service URL path
        svc_path = service_url.strip()
        if not svc_path.startswith("/"):
            svc_path = "/" + svc_path
        full_url = f"{base_url}{svc_path}"

    log.info(f"Discovering entity sets from: {full_url}")

    try:
        # Try the service root - it lists available collections
        resp = session.get(full_url, params={"$format": "json"}, timeout=SAP["timeout"])
        resp.raise_for_status()

        data = resp.json().get("d", {})
        entity_sets = data.get("EntitySets", [])

        if entity_sets:
            log.info(f"  Found {len(entity_sets)} entity sets")
            return entity_sets

        # Fallback: check if there's a collections list
        collections = []
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict) and "url" in item:
                            collections.append(item["url"])
        if collections:
            log.info(f"  Found {len(collections)} collections from root doc")
            return collections

        log.warning(f"  No entity sets found at {full_url}")
        return []

    except Exception as e:
        log.error(f"  Failed to discover entities: {e}")
        return []


def main():
    save_mode = "--save" in sys.argv

    log.info("=" * 60)
    log.info("SAP OData Service Discovery")
    log.info(f"Server: {SAP['host']}:{SAP['port']}")
    log.info("=" * 60)

    services = discover_services()

    if not services:
        log.warning("No services found! Check SAP OData activation.")
        return

    # Print summary
    print(f"\n{'='*80}")
    print(f"  DISCOVERED {len(services)} OData SERVICES")
    print(f"{'='*80}")
    for i, svc in enumerate(services, 1):
        print(f"  {i:3d}. {svc['technical_name']:<40s} | {svc['title']}")

    # Discover entity sets for each service
    for svc in services:
        svc_url = svc.get("service_url", "")
        if svc_url:
            entities = discover_entity_sets(svc_url)
            svc["entity_sets"] = entities
        else:
            svc["entity_sets"] = []

    # Print detailed breakdown
    print(f"\n{'='*80}")
    print(f"  ENTITY SETS PER SERVICE")
    print(f"{'='*80}")
    total_entities = 0
    for svc in services:
        entities = svc.get("entity_sets", [])
        total_entities += len(entities)
        print(f"\n  {svc['technical_name']} ({len(entities)} entities):")
        for ent in entities:
            print(f"    - {ent}")

    print(f"\n  TOTAL: {len(services)} services, {total_entities} entity sets")

    if save_mode:
        with open("services.json", "w", encoding="utf-8") as f:
            json.dump(services, f, indent=2, ensure_ascii=False)
        log.info("Saved service catalog to services.json")


if __name__ == "__main__":
    main()
