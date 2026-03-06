import os
import time
import httpx
from datetime import datetime

# ==============================================================================
# 1. SAP Connection Configuration (Loaded from your .env file)
# ==============================================================================
SAP_HOST = os.getenv("SAP_HOST")
SAP_PORT = os.getenv("SAP_PORT")
SAP_USER = os.getenv("SAP_USER")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")
SAP_CLIENT = os.getenv("SAP_CLIENT", "100")

# Build the base URL, e.g., https://mysap.com:44300/sap/opu/odata/sap
SAP_BASE_URL = f"{os.getenv('SAP_PROTOCOL','https')}://{SAP_HOST}:{SAP_PORT}/sap/opu/odata/sap"

# We use Basic Authentication for the SAP requests
SAP_AUTH = (SAP_USER, SAP_PASSWORD)

# These headers tell SAP we want JSON data, not XML
SAP_HEADERS = {
    "Accept": "application/json",
    "sap-client": SAP_CLIENT
}

# ==============================================================================
# 2. Main Downloading Function
# ==============================================================================
def fetch_from_sap(service_name: str, entity: str, delta_field: str = None, since: datetime = None, max_records: int = 1000) -> list:
    """
    Connects to SAP and downloads records using HTTPX. 
    Uses SAP's 'Next Link' (Server-side paging) for the most reliable batching.
    """
    # Start URL
    current_url = f"{SAP_BASE_URL}/{service_name}/{entity}"
    
    # We use httpx.Client() for synchronous requests with modern features
    # 'verify=False' stops SSL errors if SAP certificates are self-signed
    client = httpx.Client(auth=SAP_AUTH, headers=SAP_HEADERS, verify=False, timeout=120)

    all_records = []
    
    # DELTA FILTER: If we have a 'since' date, ask SAP only for new/changed stuff
    params = {"$format": "json", "$top": 500} # Default batch size
    if since and delta_field:
        formatted_date = since.strftime("%Y-%m-%dT%H:%M:%S")
        params["$filter"] = f"{delta_field} gt datetime'{formatted_date}'"

    first_request = True
    
    try:
        while len(all_records) < max_records:
            data = {}
            # RETRY LOGIC: SAP-style retries (honor Retry-After if server is busy)
            success = False
            for attempt in range(1, 6):
                try:
                    # Use params ONLY for the first request. 
                    # Subsequent batches use the full URL from '__next' link.
                    response = client.get(current_url, params=params if first_request else None)
                    first_request = False
                    
                    # Check for "Too Many Requests" (429) or Server Busy (503)
                    if response.status_code in [429, 503]:
                        wait_time = int(response.headers.get("Retry-After", 10))
                        print(f"  [SAP] Server busy. Waiting {wait_time}s as requested by SAP...")
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json().get("d", {})
                    success = True
                    break 
                except Exception as e:
                    print(f"  [SAP] Connection Error. Retry {attempt}/5: {e}")
                    if attempt < 5:
                        time.sleep(10)
                    else:
                        raise Exception(f"Failed to reach SAP after 5 attempts: {e}")

            if not success:
                break

            # GET THE RECORDS
            results = data.get("results", [])
            if not results:
                break

            # Clean the meta data tags
            cleaned = [
                {k: v for k, v in row.items() if not k.startswith("__") and not isinstance(v, (dict, list))}
                for row in results
            ]
            all_records.extend(cleaned)

            # CHECK FOR NEXT BATCH: SAP provides a '__next' link if there is more data
            next_link = data.get("__next")
            if next_link and len(all_records) < max_records:
                current_url = next_link # Follow SAP's built-in paging link
                params = None # Parameters are already inside the next_link
            else:
                break # No more data or limit reached

    finally:
        client.close() # Always close the client connection

    return all_records[:max_records]
