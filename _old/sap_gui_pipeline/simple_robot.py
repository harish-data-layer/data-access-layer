import win32com.client
import time
import os
import pandas as pd
import psycopg2
import psycopg2.extras
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SAP_ROBOT")

POSTGRES_CONFIG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "postgres",
    "username": "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

EXPORT_FILE = r"C:\Temp\sap_export.txt"

def run_robot():
    try:
        log.info("Attaching to SAP GUI...")
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        
        # Take the first connection/session we find
        conn = app.Children(0)
        session = conn.Children(0)
        log.info("Successfully attached.")

        # Go to SE16N
        log.info("Navigating to SE16N...")
        session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
        session.findById("wnd[0]").sendVKey(0)
        time.sleep(2)

        # Table MARA
        session.findById("wnd[0]/usr/ctxtGD-TAB").text = "MARA"
        session.findById("wnd[0]").sendVKey(0)
        time.sleep(1)

        # Execute F8
        log.info("Executing query...")
        session.findById("wnd[0]").sendVKey(8)
        time.sleep(5)

        # Export to Local File
        log.info("Exporting data...")
        os.makedirs(r"C:\Temp", exist_ok=True)
        if os.path.exists(EXPORT_FILE): os.remove(EXPORT_FILE)

        session.findById("wnd[0]/mbar/menu[0]/menu[3]/menu[2]").select()
        time.sleep(1)
        session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
        session.findById("wnd[1]/tbar[0]/btn[0]").press()
        time.sleep(1)
        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = EXPORT_FILE
        session.findById("wnd[1]/tbar[0]/btn[0]").press()
        time.sleep(3)
        log.info("✅ Export complete.")

        # Sync to Postgres
        log.info("Syncing to PostgreSQL...")
        df = pd.read_csv(EXPORT_FILE, sep="\t", encoding="utf-16", dtype=str, on_bad_lines="skip")
        df.columns = [c.strip().lower() for c in df.columns]
        records = df.dropna(how="all").to_dict(orient="records")

        pg = psycopg2.connect(**POSTGRES_CONFIG)
        cur = pg.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS sap;")
        
        cols = list(records[0].keys())
        col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
        pk = cols[0]
        cur.execute(f'CREATE TABLE IF NOT EXISTS sap.MARA ({col_defs}, PRIMARY KEY ("{pk}"));')
        
        col_str = ", ".join([f'"{c}"' for c in cols])
        val_str = ", ".join([f"%({c})s" for c in cols])
        upd_str = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != pk])
        sql = f'INSERT INTO sap.MARA ({col_str}) VALUES ({val_str}) ON CONFLICT ("{pk}") DO UPDATE SET {upd_str};'
        
        psycopg2.extras.execute_batch(cur, sql, records)
        pg.commit()
        pg.close()
        log.info(f"✅ Successfully synced {len(records)} records to sap.MARA!")

    except Exception as e:
        log.error(f"❌ Robot failed: {e}")

if __name__ == "__main__":
    run_robot()
