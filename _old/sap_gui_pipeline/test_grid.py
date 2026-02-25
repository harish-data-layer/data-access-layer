import win32com.client
import time

def extract_grid():
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        connection = app.Children(0)
        session = connection.Children(0)
        
        print("Navigating to SE16N...")
        session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
        session.findById("wnd[0]").sendVKey(0)
        time.sleep(2)
        
        print("Entering MARA & Executing...")
        session.findById("wnd[0]/usr/ctxtGD-TAB").text = "MARA"
        session.findById("wnd[0]").sendVKey(8) # F8
        time.sleep(5)
        
        print("Extracting Grid...")
        grid = session.findById("wnd[0]/usr/cntlRESULT_LIST/shellcont/shell")
        print(f"✅ Grid found! Total Rows: {grid.RowCount}")
        
        # Read the first few rows
        col_names = grid.ColumnOrder
        for i in range(min(5, grid.RowCount)):
            row_data = []
            for col in col_names[:5]: # just 5 columns for test
                val = grid.GetCellValue(i, col)
                row_data.append(f"{col}: {val}")
            print(f"Row {i}: {', '.join(row_data)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_grid()
