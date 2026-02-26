"""Test all Custom API endpoints."""
import requests
import json

URL = "http://127.0.0.1:5001"

print("=" * 60)
print("  TESTING CUSTOM SAP DATA API")
print("=" * 60)

# 1. Health
print("\n[1] GET /health")
r = requests.get(f"{URL}/health")
print(f"    Status: {r.status_code} - {r.json()['status']}")

# 2. List services (search for SALES)
print("\n[2] GET /services?search=SALES")
r = requests.get(f"{URL}/services", params={"search": "SALES"})
d = r.json()
print(f"    Found {d['total']} services with 'SALES':")
for s in d["services"]:
    print(f"      - {s['name']}")

# 3. List entities for a service
print("\n[3] GET /services/ZAPI_SALES_ORDER_SRV/entities")
r = requests.get(f"{URL}/services/ZAPI_SALES_ORDER_SRV/entities")
d = r.json()
print(f"    Service: {d.get('service')}")
print(f"    Found {d.get('total', 0)} entities:")
for e in d.get("entities", [])[:5]:
    print(f"      - {e}")
if d.get("total", 0) > 5:
    print(f"      ... and {d['total'] - 5} more")

# 4. PULL data
print("\n[4] POST /pull (pulling 5 sales orders)")
r = requests.post(f"{URL}/pull", json={
    "service_path": "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
    "entity_name": "A_SalesOrder",
    "top": 5,
    "save_to_db": False,
    "called_by": "test_script"
})
d = r.json()
print(f"    Log ID: {d.get('log_id')}")
print(f"    Status: {d.get('status')}")
print(f"    Records: {d.get('records_count')}")
if d.get("data"):
    first = d["data"][0]
    print(f"    First record keys: {list(first.keys())[:6]}...")

# 5. PUSH UPDATE (update a real sales order)
print("\n[5] POST /push/update (updating Sales Order '2')")
r = requests.post(f"{URL}/push/update", json={
    "service_path": "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
    "entity_with_key": "A_SalesOrder('2')",
    "mata_id": "2",
    "payload": {"PurchaseOrderByCustomer": "CUSTOM_API_TEST"},
    "called_by": "test_script"
}, timeout=180)
d = r.json()
print(f"    Log ID: {d.get('log_id')}")
print(f"    Status: {d.get('status')}")
print(f"    HTTP Code: {d.get('status_code')}")
if d.get("status") == "SUCCESS":
    print("    >>> SAP UPDATE SUCCESSFUL! <<<")

# 6. Check logs
print("\n[6] GET /logs")
r = requests.get(f"{URL}/logs")
d = r.json()
print(f"    Total operations: {d['total']}")
print(f"    Summary: {d['summary']}")

print("\n" + "=" * 60)
print("  ALL TESTS COMPLETE!")
print("=" * 60)
