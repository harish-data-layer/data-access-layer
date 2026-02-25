import win32com.client

def test_rfc():
    functions = win32com.client.Dispatch("SAP.Functions")
    conn = functions.Connection
    
    conn.Destination = "S4hana"
    conn.Client = "100"
    conn.User = "alagan"
    conn.Password = "hana@123"
    conn.Language = "EN"
    
    print("Connecting via Destination S4hana...")
    if conn.Logon(0, True):
        print("✅ Successfully connected via RFC!")
        conn.Logoff()
    else:
        print("❌ Failed to connect.")

if __name__ == "__main__":
    test_rfc()
