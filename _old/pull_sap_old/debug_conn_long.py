import requests
from requests.auth import HTTPBasicAuth

# Try Port 8000 with a VERY long timeout
url = "http://s1.mncinfosys.com:8000/sap/opu/odata/sap/API_PRODUCT_SRV/$metadata"
auth = HTTPBasicAuth("alagan", "hana@123")

print(f"Testing {url} with 60s timeout...")
try:
    resp = requests.get(url, auth=auth, timeout=60)
    print(f"Status: {resp.status_code}")
    print(f"Content length: {len(resp.content)}")
except Exception as e:
    print(f"Failed: {e}")
