import requests
from requests.auth import HTTPBasicAuth

# Try SAP Ping
url = "http://s1.mncinfosys.com:8000/sap/bc/ping"
auth = HTTPBasicAuth("alagan", "hana@123")

print(f"Pinging {url}...")
try:
    resp = requests.get(url, auth=auth, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Failed: {e}")
