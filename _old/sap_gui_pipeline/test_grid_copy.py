import win32com.client
import time

def main():
    sap_gui = win32com.client.GetObject("SAPGUI")
    app = sap_gui.GetScriptingEngine
    session = app.Children(0).Children(0)
    
    grid = session.findById("wnd[0]/shellcont/shell")
    col_names = grid.ColumnOrder
    
    print("Testing scroll over 500...")
    for i in range(500, 505):
        try:
            grid.setCurrentCell(i, col_names[0])
            val = grid.GetCellValue(i, col_names[0])
            print(f"Row {i} - {col_names[0]}: {val}")
        except Exception as e:
            print(f"Row {i} error: {e}")

if __name__ == "__main__":
    main()
