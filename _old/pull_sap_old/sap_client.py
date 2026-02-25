import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional
from logger import get_logger
from config import SAP

log = get_logger("SAP")

class SAPClient:
    def __init__(self):
        # We will try these common SAP OData ports if the default fails
        # Instance 40 usually uses 8040, 44340, 3240 (dispatcher), 3340 (RFC)
        self.ports = ["8040", "8000", "443", "3240", "3340", "8140", "44340"] 
        self.base_host = "s1.mncinfosys.com"
        self.base_ip = "49.205.65.5" # Fallback IP if DNS is weird
        self.timeout = 15
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(SAP["username"], SAP["password"])
        self.session.headers.update({
            "Accept":       "application/json",
            "Content-Type": "application/json",
            "sap-client":   SAP["client"],
        })
        self.active_url = None

    def _find_active_url(self, service_path):
        """Tests different ports to find the one that is actually open."""
        protocols = ["http", "https"]
        hosts = [self.base_host, self.base_ip]
        
        for host in hosts:
            for proto in protocols:
                for port in self.ports:
                    url = f"{proto}://{host}:{port}{service_path}"
                    log.info(f"Testing connection: {url}...")
                    try:
                        # We just try to fetch the service metadata to see if it responds
                        resp = self.session.get(url, timeout=5, headers={"x-csrf-token": "Fetch"}, verify=False)
                        # We accept 200, 401 (Auth required), 403 (Token missing), or even 404
                        if resp.status_code < 500:
                            log.info(f"✅ Success! Host {host} on Port {port} is talking ({proto}). Status: {resp.status_code}")
                            self.active_url = f"{proto}://{host}:{port}"
                            return self.active_url
                    except Exception:
                        continue
        
        raise ConnectionError(f"❌ Could not connect to SAP at {self.base_host} on any common OData ports. Please check if OData is enabled for instance 40.")

    def _get_csrf_token(self, service_path: str) -> str:
        if not self.active_url:
            self._find_active_url(service_path)
            
        url = f"{self.active_url}{service_path}"
        resp = self.session.get(url, headers={"x-csrf-token": "Fetch"}, timeout=SAP["timeout"])
        token = resp.headers.get("x-csrf-token")
        if not token:
            raise RuntimeError("CSRF token fetch failed - check SAP credentials.")
        return token

    def pull_via_gui(self, table_name: str, max_rows: int = 1000) -> list:
        """Fallback method: Pulls data using SAP GUI Scripting (COM)."""
        import win32com.client
        import time
        
        log.info(f"🚀 SAP GUI Fallback: Attempting to pull {table_name} via GUI Scripting...")
        try:
            sap_gui = win32com.client.GetObject("SAPGUI")
            app = sap_gui.GetScriptingEngine
            session = app.Children(0).Children(0)
            
            # Navigate to SE16N
            session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
            session.findById("wnd[0]").sendVKey(0)
            time.sleep(1)
            
            # Enter Table
            session.findById("wnd[0]/usr/ctxtGD-TAB").text = table_name
            if max_rows:
                try:
                    session.findById("wnd[0]/usr/txtGD-MAX_LINES").text = str(max_rows)
                except: pass
            
            # Execute
            session.findById("wnd[0]").sendVKey(8)
            time.sleep(3)
            
            # Find Grid
            grid = None
            for candidate in ["wnd[0]/shellcont/shell", "wnd[0]/usr/cntlRESULT_LIST/shellcont/shell"]:
                try:
                    grid = session.findById(candidate)
                    break
                except: pass
            
            if not grid:
                raise RuntimeError("Could not find data grid in SAP GUI.")
            
            total_rows = grid.RowCount
            col_names = grid.ColumnOrder
            log.info(f"✅ Found {total_rows} rows in GUI. Extraction started...")
            
            records = []
            for i in range(min(total_rows, max_rows if max_rows else 999999)):
                # Lazy loading scroll
                if i > 0 and i % 50 == 0:
                    try: grid.setCurrentCell(i, col_names[0])
                    except: pass
                
                row = {}
                for col in col_names:
                    row[col] = grid.GetCellValue(i, col)
                records.append(row)
                
                if i > 0 and i % 200 == 0:
                    log.info(f"  ...extracted {i}/{total_rows} rows")
                    
            return records
            
        except Exception as e:
            log.error(f"❌ SAP GUI extraction failed: {e}")
            raise

    def pull(self, service_path: str, entity: str, params: dict = None) -> list:
        # First try OData
        try:
            return self._pull_odata(service_path, entity, params)
        except Exception as e:
            log.warning(f"⚠️ OData pull failed ({e}). Falling back to SAP GUI...")
            # Map entity to physical table
            table_map = {"A_Product": "MARA"} 
            table_name = table_map.get(entity, "MARA")
            return self.pull_via_gui(table_name)

    def _pull_odata(self, service_path: str, entity: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.active_url:
            self._find_active_url(service_path)

        url = f"{self.active_url}{service_path}/{entity}"
        all_records: List[Dict[str, Any]] = []
        query: Dict[str, Any] = {"$format": "json", "$top": 1000}
        if params:
            query.update(params)

        while url:
            log.info(f"Pulling: {entity} | URL: {url}")
            try:
                resp = self.session.get(url, params=query, timeout=SAP["timeout"])
                resp.raise_for_status()
                data = resp.json().get("d", {})
                records = data.get("results", [])
                all_records.extend(records)
                log.info(f"  Received {len(records)} records.")

                url = data.get("__next")
                query = {} 
            except Exception as e:
                log.error(f"Error pulling from SAP: {e}")
                raise
        return all_records

    def push_update(self, service_path: str, entity_with_key: str, payload: dict):
        if not self.active_url:
            self._find_active_url(service_path)
            
        token = self._get_csrf_token(service_path)
        url = f"{self.active_url}{service_path}/{entity_with_key}"
        resp = self.session.patch(
            url, json=payload,
            headers={"x-csrf-token": token},
            params={"$format": "json"},
            timeout=SAP["timeout"]
        )
        resp.raise_for_status()
        return resp.status_code
