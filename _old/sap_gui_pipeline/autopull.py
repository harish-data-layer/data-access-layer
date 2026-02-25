import win32com.client
import time
import psycopg2
import psycopg2.extras
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("SAP_AUTOPULL")

DB_CONFIG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "postgres",
    "user": "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

def pull_table_headless(table_name="MARA"):
    log.info(f"Starting fully automated pull for {table_name}...")
    
    # 1. Connect to SAP seamlessly
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        session = app.Children(0).Children(0)
    except Exception:
        log.error("Could not find SAP session. Make sure SAP is open and you are logged in.")
        return

    # 2. Navigate exactly to what we want
    log.info("Navigating to SE16N...")
    session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
    session.findById("wnd[0]").sendVKey(0) # Enter
    time.sleep(1)
    
    # Close popup if one appears
    if session.ActiveWindow.Name != "wnd[0]":
        session.ActiveWindow.sendVKey(0)

    log.info(f"Entering Table: {table_name}")
    session.findById("wnd[0]/usr/ctxtGD-TAB").text = table_name
    
    # Clear max rows for full extraction
    try:
        session.findById("wnd[0]/usr/txtGD-MAX_LINES").text = ""
    except:
        pass
        
    log.info("Executing Search (F8)...")
    session.findById("wnd[0]").sendVKey(8)
    time.sleep(5) # Give it time to load data
    
    # 3. Read directly from the SAP memory grid (Zero Popups/Clipboards)
    grid = None
    grid_candidates = [
        "wnd[0]/shellcont/shell", # <-- YOUR EXACT GRID ID!
        "wnd[0]/usr/cntlRESULT_LIST/shellcont/shell",
        "wnd[0]/usr/cntlGRID1/shellcont/shell",
        "wnd[0]/usr/cntlCUSTOM/shellcont/shell", 
        "wnd[0]/usr/cntlALV_GRID/shellcont/shell",
        "wnd[0]/usr/cntlCONTAINER/shellcont/shell"
    ]
    
    for _ in range(3): # Retry finding grid up to 3 times (15 seconds total)
        for candidate in grid_candidates:
            try:
                grid = session.findById(candidate)
                break
            except:
                pass
        if grid:
            break
        time.sleep(5)
        
    if not grid:
        log.error("Could not find the data grid on the screen. Did the search return any results?")
        return

    try:
        total_rows = grid.RowCount
        log.info(f"✅ Found {total_rows} records in SAP memory. Reading now (this may take a minute)...")
        
        # Get column names
        col_names = grid.ColumnOrder
        
        # Read all rows into memory
        records = []
        for i in range(total_rows):
            # ALV grids "lazy load" data. We need to scroll down to force it to load.
            if i > 0 and i % 50 == 0:
                try:
                    grid.setCurrentCell(i, col_names[0])
                except Exception as e:
                    pass
                
            row_dict = {}
            for col in col_names:
                row_dict[col.strip().lower().replace("/", "_")] = grid.GetCellValue(i, col)
            records.append(row_dict)
            
            if i > 0 and i % 100 == 0:
                log.info(f"  ...read {i}/{total_rows} rows")
                
    except Exception as e:
        log.error(f"Failed to read Grid data. Are there too many rows? Error: {e}")
        return

    if not records:
        log.warning("No data found!")
        return

    # 4. Save to Database
    log.info("Uploading data to PostgreSQL...")
    pg = psycopg2.connect(**DB_CONFIG)
    cur = pg.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS sap;")
    
    cols = list(records[0].keys())
    # Find a primary key candidate (usually the first column, e.g., matnr)
    pk = cols[1] if len(cols) > 1 and "mandt" in cols[0].lower() else cols[0]
    
    col_defs = ", ".join([f'"{c}" TEXT' for c in cols])
    cur.execute(f'CREATE TABLE IF NOT EXISTS sap.{table_name} ({col_defs}, PRIMARY KEY ("{pk}"));')
    
    col_str = ", ".join([f'"{c}"' for c in cols])
    val_str = ", ".join([f"%({c})s" for c in cols])
    upd_str = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != pk])
    sql = f'INSERT INTO sap.{table_name} ({col_str}) VALUES ({val_str}) ON CONFLICT ("{pk}") DO UPDATE SET {upd_str};'
    
    psycopg2.extras.execute_batch(cur, sql, records)
    pg.commit()
    pg.close()
    
    log.info(f"🎉 100% AUTOMATED SUCCESS: {len(records)} records synced from SAP to database!")

if __name__ == "__main__":
    import sys
    # Allow passing table name as argument (e.g., python autopull.py MARA)
    table = sys.argv[1] if len(sys.argv) > 1 else "MARA"
    pull_table_headless(table)
