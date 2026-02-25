import win32com.client
import win32clipboard
import time
import pandas as pd
import psycopg2
import psycopg2.extras
import logging
import io

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("SAP_SMART_SYNC")

DB_CONFIG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "postgres",
    "user": "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

def get_clipboard():
    win32clipboard.OpenClipboard()
    try:
        return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

def run_smart_sync():
    try:
        log.info("Connecting to SAP...")
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        connection = app.Children(0)
        session = connection.Children(0)

        # Handle any blocking popups (like the 'Number of Entries' box)
        if connection.Children.Count > 1:
            log.info("Closing popup window...")
            connection.Children(1).sendVKey(0) # Press Enter on popup
            time.sleep(1)

        # 1. Execute
        log.info("Executing MARA report...")
        session.findById("wnd[0]").sendVKey(8) # F8
        time.sleep(5)

        # 2. Select All & Copy (The most reliable way)
        log.info("Preparing clipboard...")
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()

        log.info("Copying data to clipboard from SAP...")
        # Use the ALV Copy shortcut
        try:
            session.findById("wnd[0]/tbar[0]/okcd").text = "&PC"
            session.findById("wnd[0]").sendVKey(0)
            time.sleep(2)
        except Exception:
            session.findById("wnd[0]/tbar[0]/okcd").text = "%PC"
            session.findById("wnd[0]").sendVKey(0)
            time.sleep(2)
            
        raw_data = ""
        try:
            raw_data = get_clipboard()
        except:
            pass

        if not raw_data or len(raw_data) < 10:
            log.error("Clipboard empty! The SAP copy command didn't work.")
            log.info("Please manually select the table in SAP, press Ctrl+C, then run this script again.")
            return

        # Check if this is actual tabular data (should have tabs)
        if "\t" not in raw_data:
            log.error(f"Clipboard has data, but it doesn't look like an SAP table. Preview: {raw_data[:100]}")
            return

        # 3. DB Sync
        df = pd.read_csv(io.StringIO(raw_data), sep="\t", dtype=str, on_bad_lines="skip")
        df.columns = [c.strip().lower().replace("/", "_") for c in df.columns]
        records = df.dropna(how="all").to_dict(orient="records")

        log.info(f"Uploading {len(records)} records to Postgres...")
        pg = psycopg2.connect(**DB_CONFIG)
        cur = pg.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS sap;")
        
        cols = list(records[0].keys())
        pk = cols[0]
        col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
        cur.execute(f'CREATE TABLE IF NOT EXISTS sap.MARA ({col_defs}, PRIMARY KEY ("{pk}"));')
        
        col_str = ", ".join([f'"{c}"' for c in cols])
        val_str = ", ".join([f"%({c})s" for c in cols])
        upd_str = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != pk])
        sql = f'INSERT INTO sap.MARA ({col_str}) VALUES ({val_str}) ON CONFLICT ("{pk}") DO UPDATE SET {upd_str};'
        
        psycopg2.extras.execute_batch(cur, sql, records)
        pg.commit()
        log.info(f"✅ SUCCESS! Synced {len(records)} records.")

    except Exception as e:
        log.error(f"❌ Failed: {e}")

if __name__ == "__main__":
    run_smart_sync()
