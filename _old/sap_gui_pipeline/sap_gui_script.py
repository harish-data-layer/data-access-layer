# =============================================================
#  sap_gui_script.py — SAP GUI Automation → PostgreSQL
# =============================================================

import win32com.client
import subprocess
import time
import os
import pandas as pd
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sap_gui_sync.log")
    ]
)
log = logging.getLogger(__name__)

# =============================================================
#  CONFIGURATION
# =============================================================

SAP_CONFIG = {
    "sap_logon_path":  r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe",
    "connection_name": "S4hana",  
    "username": "alagan",
    "password": "hana@123",
    "client":   "100",
}

POSTGRES_CONFIG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "postgres",
    "username": "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

SAP_TABLE   = "MARA"
PG_TABLE    = "MARA"
EXPORT_FILE = r"C:\Temp\sap_mara_export.txt"

def get_sap_session():
    """Finds an existing session or creates one."""
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        
        # Look for ANY open session
        for conn in app.Children:
            if conn.Children.Count > 0:
                session = conn.Children(0)
                log.info(f"✅ Found existing connection '{conn.Description}'. Mapping session...")
                return session
        
        # No session? Try to open S4hana
        log.info(f"Opening connection: {SAP_CONFIG['connection_name']}")
        conn = app.OpenConnection(SAP_CONFIG["connection_name"], True)
        
        # Wait up to 15 seconds for session to appear
        for _ in range(15):
            if conn.Children.Count > 0:
                session = conn.Children(0)
                log.info("Session window detected.")
                break
            time.sleep(1)
        else:
            raise RuntimeError("SAP opened but the session window never appeared.")
            
        # Try to login if we see the login screen fields
        log.info("Checking for login screen...")
        try:
            # These are the standard IDs for the login screen
            session.findById("wnd[0]/usr/txtRSYST-BNAME").text = SAP_CONFIG["username"]
            session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = SAP_CONFIG["password"]
            session.findById("wnd[0]").sendVKey(0) # Enter
            log.info("Credentials sent.")
            time.sleep(5)
        except Exception:
            log.info("Already at main screen or login fields not found.")
            
        return session

    except Exception as e:
        log.error(f"SAP Session error: {e}")
        raise

def run_extraction(session):
    log.info(f"Starting SE16N extraction for {SAP_TABLE}")
    
    # Go to SE16N
    session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
    session.findById("wnd[0]").sendVKey(0)
    time.sleep(2)

    # Enter table
    session.findById("wnd[0]/usr/ctxtGD-TAB").text = SAP_TABLE
    session.findById("wnd[0]").sendVKey(0)
    time.sleep(1)

    # Execute
    log.info("Executing...")
    session.findById("wnd[0]").sendVKey(8)
    time.sleep(5)

    # Export
    log.info("Exporting to local file...")
    os.makedirs(os.path.dirname(EXPORT_FILE), exist_ok=True)
    if os.path.exists(EXPORT_FILE):
        os.remove(EXPORT_FILE)

    # Menu: Table Entry -> Export -> Local File
    session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[2]").select()
    time.sleep(1)
    
    # Select "Unconverted"
    session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    time.sleep(1)

    # Set filename and save
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = EXPORT_FILE
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    time.sleep(2)
    
    log.info(f"✅ Data saved to {EXPORT_FILE}")
    return EXPORT_FILE

def sync_to_db(file_path):
    log.info("Parsing data and syncing to PostgreSQL...")
    
    # Read (SAP uses UTF-16 for unconverted exports usually)
    try:
        df = pd.read_csv(file_path, sep="\t", encoding="utf-16", dtype=str, on_bad_lines="skip")
    except Exception:
        df = pd.read_csv(file_path, sep="\t", encoding="cp1252", dtype=str, on_bad_lines="skip")

    df.columns = [c.strip().lower() for c in df.columns]
    records = df.dropna(how="all").to_dict(orient="records")

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    # Ensure schema
    cur.execute("CREATE SCHEMA IF NOT EXISTS sap;")
    
    # Create table
    cols = list(records[0].keys())
    col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
    pk = cols[0] # assuming MATNR is first
    
    cur.execute(f'CREATE TABLE IF NOT EXISTS sap."{PG_TABLE}" ({col_defs}, PRIMARY KEY ("{pk}"));')
    
    # Upsert
    col_str = ", ".join([f'"{c}"' for c in cols])
    val_str = ", ".join([f"%({c})s" for c in cols])
    upd_str = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != pk])

    sql = f'INSERT INTO sap."{PG_TABLE}" ({col_str}) VALUES ({val_str}) ON CONFLICT ("{pk}") DO UPDATE SET {upd_str};'
    
    psycopg2.extras.execute_batch(cur, sql, records)
    conn.commit()
    conn.close()
    
    log.info(f"✅ Synced {len(records)} records to sap.{PG_TABLE}!")
    return len(records)

if __name__ == "__main__":
    try:
        session = get_sap_session()
        file = run_extraction(session)
        sync_to_db(file)
    except Exception as e:
        log.error(f"Pipeline failed: {e}")
