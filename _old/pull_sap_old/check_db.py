import psycopg2

PG = {
    "host":     "4.240.80.20",
    "port":     5432,
    "database": "postgres",
    "user":     "postgres_admin",
    "password": "N2kGTbsE&s@nwmw6wA5JKk&#*iDTxAkmcjbGywF#SXMWz&SqXd",
}

conn = psycopg2.connect(**PG)
cur = conn.cursor()

cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'sap' ORDER BY table_name;
""")
rows = cur.fetchall()
print(f"Tables in sap schema ({len(rows)}):")
for row in rows:
    print(f"  {row[0]}")

conn.close()
