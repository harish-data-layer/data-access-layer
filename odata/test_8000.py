import requests
from requests.auth import HTTPBasicAuth

url = "http://s1.mncinfosys.com:8000/sap/opu/odata/sap/API_PRODUCT_SRV"
auth = HTTPBasicAuth('alagan', 'hana@123')

print(f"Testing OData on port 8000: {url}")
try:
    resp = requests.get(url, auth=auth, timeout=10, verify=False)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("SUCCESS! OData is reachable on port 8000.")
    else:
        print(f"Server responded with: {resp.text[:200]}")
except Exception as e:
    print(f"Connection failed: {e}")
