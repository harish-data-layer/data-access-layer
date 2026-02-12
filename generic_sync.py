import json
import psycopg2

# =============================
# LOAD CONFIG
# =============================

with open("config.json") as f:
    config = json.load(f)

src = config["source_db"]
tgt = config["target_db"]

# =============================
# CONNECT DATABASES
# =============================

source_conn = psycopg2.connect(
    host=src["host"],
    port=src["port"],
    database=src["database"],
    user=src["user"],
    password=src["password"]
)

target_conn = psycopg2.connect(
    host=tgt["host"],
    port=tgt["port"],
    database=tgt["database"],
    user=tgt["user"],
    password=tgt["password"]
)

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

print("✅ Connected to both DBs")

# =============================
# GENERIC TABLE SYNC LOOP
# =============================

for table in config["tables"]:
    src_table = table["source_table"]
    tgt_table = table["target_table"]
    cols = table["columns"]

    print(f"🔄 Syncing {src_table} → {tgt_table}")

    # Extract
    source_cursor.execute(f"SELECT {', '.join(cols)} FROM {src_table}")
    rows = source_cursor.fetchall()

    # Load
    placeholders = ", ".join(["%s"] * len(cols))
    columns_str = ", ".join(cols)

    insert_query = f"""
        INSERT INTO "{tgt_table}"({columns_str})
        VALUES ({placeholders})
    """

    for row in rows:
        target_cursor.execute(insert_query, row)

    target_conn.commit()
    print(f"✅ {tgt_table} synced")

# =============================
# CLOSE CONNECTIONS
# =============================

source_cursor.close()
target_cursor.close()

source_conn.close()
target_conn.close()

print("🎉 ALL TABLES SYNCED SUCCESSFULLY")
