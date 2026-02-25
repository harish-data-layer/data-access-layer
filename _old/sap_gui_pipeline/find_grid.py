import win32com.client

def get_grid_tree():
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        app = sap_gui.GetScriptingEngine
        session = app.Children(0).Children(0)
        
        print("Scanning SAP Screen...")
        print(f"Transaction: {session.Info.Transaction}")
        
        found_shells = []
        
        def walk(parent):
            try:
                if not hasattr(parent, "Children"): return
                children = getattr(parent, "Children", None)
                if children is None: return
                count = getattr(children, "Count", 0)
                
                for i in range(count):
                    child = children(i)
                    ctype = getattr(child, "Type", "")
                    cid = getattr(child, "ID", "")
                    csubtype = getattr(child, "SubType", "")
                    
                    if ctype == "GuiShell":
                        found_shells.append((cid, csubtype))
                        print(f"✅ Found GuiShell -> ID: {cid} | SubType: {csubtype}")
                    elif "GRID" in cid.upper() or "RESULT" in cid.upper() or "ALV" in cid.upper() or "SHELL" in cid.upper():
                        print(f"Interesting ID -> {cid} (Type: {ctype})")
                        
                    walk(child)
            except Exception as e:
                pass

        walk(session.findById("wnd[0]"))
        
        print(f"\nTotal Grids found: {len(found_shells)}")

    except Exception as e:
        print(f"Main Error: {e}")

if __name__ == "__main__":
    get_grid_tree()
