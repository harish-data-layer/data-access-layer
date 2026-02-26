#!/usr/bin/env python3
"""Quick test with the actual Z-prefixed service name from SAP catalog."""
import json
import requests

API_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("  TESTING WITH ACTUAL SAP SERVICE NAME")
print("=" * 60)

# Test 1: Read from SAP first (GET - this we know works)
print("\n[TEST 1] Read from SAP (to confirm connection)...")
import urllib3; urllib3.disable_warnings()
from requests.auth import HTTPBasicAuth

sap_url = "https://s1.mncinfosys.com:44329/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder"
s = requests.Session()
s.auth = HTTPBasicAuth("alagan", "hana@123")
s.headers.update({"sap-client": "100", "Accept": "application/json"})
s.verify = False

r = s.get(sap_url, params={"$format": "json", "$top": 1}, timeout=30)
print(f"  GET Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("d", {}).get("results", [])
    if data:
        order = data[0]
        so_id = order.get("SalesOrder", "")
        print(f"  Found real Sales Order: {so_id}")
        print(f"  Fields: {list(order.keys())[:6]}...")
        
        # Test 2: Try UPDATE on this real order via our API
        print(f"\n[TEST 2] Updating Sales Order '{so_id}' via Push API...")
        update_data = {
            "service_path": "/sap/opu/odata/sap/API_SALES_ORDER_SRV",
            "entity_with_key": f"A_SalesOrder('{so_id}')",
            "mata_id": so_id,
            "payload": {
                "PurchaseOrderByCustomer": "AI_PUSH_TEST"
            },
            "pushed_by": "proof_test_v2"
        }
        r2 = requests.post(f"{API_URL}/push/update", json=update_data, timeout=60)
        result = r2.json()
        print(f"  Push ID: {result.get('push_id')}")
        print(f"  Status: {result.get('status')}")
        print(f"  HTTP Code: {result.get('status_code')}")
        if result.get('status') == 'SUCCESS':
            print("  >>> SAP UPDATE SUCCESSFUL! <<<")
        elif result.get('error'):
            error_text = result['error'][:200]
            print(f"  SAP says: {error_text}")
    else:
        print("  No sales orders found")
else:
    print(f"  Error: {r.status_code}")

# Test 3: Check all statuses
print("\n[TEST 3] Push status summary...")
r3 = requests.get(f"{API_URL}/push/status")
data = r3.json()
print(f"  Total pushes: {data['total']}")
print(f"  Summary: {data['summary']}")

print("\n" + "=" * 60)
