import win32com.client
import sys

def list_controls(session, parent_id, depth=0, f=None):
    try:
        parent = session.findById(parent_id)
        if hasattr(parent, "Children"):
            for i in range(parent.Children.Count):
                child = parent.Children(i)
                text = ""
                try: text = getattr(child, 'Text', '')
                except: pass
                
                info = "  " * depth + f"-> ID: {child.ID}, Type: {child.Type}, Text: {text}\n"
                f.write(info)
                
                list_controls(session, child.ID, depth + 1, f)
    except Exception as e:
        pass

def spy():
    print("Navigating to MARA...")
    sap_gui = win32com.client.GetObject("SAPGUI")
    app = sap_gui.GetScriptingEngine
    session = app.Children(0).Children(0)
    
    # Navigate
    session.findById("wnd[0]/tbar[0]/okcd").text = "/nSE16N"
    session.findById("wnd[0]").sendVKey(0)
    import time; time.sleep(1)
    
    session.findById("wnd[0]/usr/ctxtGD-TAB").text = "MARA"
    try:
        session.findById("wnd[0]/usr/txtGD-MAX_LINES").text = "10"
    except:
        pass
        
    print("Executing (F8)...")
    session.findById("wnd[0]").sendVKey(8)
    time.sleep(3)
    
    print("Dumping Screen...")
    with open("spy_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Transaction: {session.Info.Transaction}\n")
        list_controls(session, "wnd[0]/usr", f=f)
    print("Done! Check spy_output.txt")

if __name__ == "__main__":
    spy()
