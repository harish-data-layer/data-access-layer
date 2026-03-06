import os
import time
import httpx
from datetime import datetime
import urllib3

urllib3.disable_warnings()

# 1. SAP Config (Loaded from .env)
SAP_BASE = f"{os.getenv('SAP_PROTOCOL', 'https')}://{os.getenv('SAP_HOST')}:{os.getenv('SAP_PORT')}/sap/opu/odata/sap"
SAP_AUTH = (os.getenv('SAP_USER'), os.getenv('SAP_PASSWORD'))
SAP_HEADERS = {"Accept": "application/json", "sap-client": os.getenv("SAP_CLIENT", "100")}

def fetch_from_sap(service: str, entity: str, delta_field: str = None, since: datetime = None, max_records: int = 1000) -> list:
    """
    Crisp & Clean SAP Puller:
    - Uses SAP's native batching (__next links) automatically.
    - Handles custom date pulling seamlessly.
    - Built-in 5x retry logic with SAP's 'Retry-After' support.
    """
    url = f"{SAP_BASE}/{service}/{entity}"
    params = {"$format": "json"}

    # DELTA/DATE PULL: Apply the date filter if requested
    if since and delta_field:
        params["$filter"] = f"{delta_field} gt datetime'{since.strftime('%Y-%m-%dT%H:%M:%S')}'"

    records = []
    
    with httpx.Client(auth=SAP_AUTH, headers=SAP_HEADERS, verify=False, timeout=120) as client:
        # Loop until SAP has no more data, or we hit max records
        while url and len(records) < max_records:
            
            # 5x SAP Retry Mechanism
            for attempt in range(5):
                try:
                    # Pass params only on the first run; __next link has them built-in later
                    res = client.get(url, params=params if not records else None)
                    
                    if res.status_code in [429, 503]: # Server busy
                        time.sleep(int(res.headers.get("Retry-After", 10)))
                        continue
                        
                    res.raise_for_status()
                    data = res.json().get("d", {})
                    break # Success! Break retry loop
                except Exception as e:
                    if attempt == 4: raise Exception(f"SAP failed after 5 tries: {e}")
                    print(f"  [SAP] Retry {attempt+1}/5 due to: {e}")
                    time.sleep(10)

            # Clean and store the batch
            batch = [{k: v for k, v in r.items() if not k.startswith("__") and not isinstance(v, (dict, list))} 
                     for r in data.get("results", [])]
            
            if not batch: break # No more data to pull!
            
            records.extend(batch)
            print(f"  [SAP] Fetched {len(batch)} records... (Total: {len(records)})")
            
            # MAGIC PAGING: SAP gives us the exact URL for the next batch via '__next'
            url = data.get("__next")

    return records[:max_records]
