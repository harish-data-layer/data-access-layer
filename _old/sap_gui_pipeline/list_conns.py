import win32com.client
import time

def list_sap_connections():
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        
        print("--- Active Connections ---")
        for i in range(app.Children.Count):
            conn = app.Children(i)
            print(f"Connection {i}: {conn.Description}")
            for j in range(conn.Children.Count):
                sess = conn.Children(j)
                print(f"  Session {j}: User={sess.Info.User}, Transaction={sess.Info.Transaction}")
    except Exception as e:
        print(f"Error accessing SAP GUI: {e}")

if __name__ == "__main__":
    list_sap_connections()
