import json
import psycopg2
import requests
import pandas as pd

# =============================
# LOAD CONFIG
# =============================

with open("config_loader.json") as f:
    config = json.load(f)

target = config["target_db"]

# =============================
# CONNECT TARGET DAL DATABASE
# =============================

conn = psycopg2.connect(
    host=target["host"],
    port=target["port"],
    database=target["database"],
    user=target["user"],
    password=target["password"]
)

cursor = conn.cursor()
print("✅ Connected to DAL database")

# =============================
# FUNCTION — INSERT DATA GENERICALLY
# =============================

def insert_data(table, columns, rows):
    cols = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    query = f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})'

    for row in rows:
        cursor.execute(query, row)

    conn.commit()
    print(f"✅ Inserted into {table}")

# =============================
# STEP 1 — LOAD FROM EXCEL
# =============================

if "excel" in config:

    print("📂 Loading from Excel...")

    excel_file = config["excel"]["file"]
    sheets = config["excel"]["tables"]

    for table in sheets:
        sheet_name = table["sheet"]
        target_table = table["target_table"]
        columns = table["columns"]

        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        rows = []
        for _, row in df.iterrows():
            rows.append(tuple(row[col] for col in columns))

        insert_data(target_table, columns, rows)

# =============================
# STEP 2 — LOAD FROM SAP API
# =============================

if "sap_api" in config:

    print("🌐 Loading from SAP API...")

    api_tables = config["sap_api"]["tables"]

    for table in api_tables:
        url = table["endpoint"]
        target_table = table["target_table"]
        columns = table["columns"]

        response = requests.get(url)
        data = response.json()

        rows = []
        for item in data:
            rows.append(tuple(item.get(col) for col in columns))

        insert_data(target_table, columns, rows)

# =============================
# CLOSE CONNECTION
# =============================

cursor.close()
conn.close()

print("🎉 ALL DATA IMPORT COMPLETED")
