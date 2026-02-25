import requests
from requests.auth import HTTPBasicAuth

url = "http://s1.mncinfosys.com:8000/sap/opu/odata/sap/API_PRODUCT_SRV/$metadata"
auth = HTTPBasicAuth("alagan", "hana@123")

print(f"Testing {url}...")
try:
    resp = requests.get(url, auth=auth, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {resp.headers}")
except Exception as e:
    print(f"Failed: {e}")

url_https = "https://s1.mncinfosys.com:8000/sap/opu/odata/sap/API_PRODUCT_SRV/$metadata"
print(f"\nTesting {url_https}...")
try:
    resp = requests.get(url_https, auth=auth, timeout=10, verify=False)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {resp.headers}")
except Exception as e:
    print(f"Failed: {e}")
