import psycopg2, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cur = conn.cursor()

print("=" * 55)
print("   DATABASE:", os.getenv('DB_NAME'), "@", os.getenv('DB_HOST'))
print("=" * 55)

# 1. Confirm schema
cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'fastapi';")
schema = cur.fetchone()
print(f"\n Schema 'fastapi' exists: {'YES ✓' if schema else 'NO ✗'}")

# 2. Both tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'fastapi';")
tables = cur.fetchall()
print(f"\n Tables in 'fastapi' schema:")
for t in tables:
    print(f"   - fastapi.{t[0]}")

# 3. incoming_requests data
print("\n" + "=" * 55)
print("   TABLE: fastapi.incoming_requests")
print("=" * 55)
cur.execute("SELECT invoice_number, status, source_ip, received_at, total_amount, currency FROM fastapi.incoming_requests ORDER BY received_at DESC;")
rows = cur.fetchall()
print(f"Total rows: {len(rows)}")
for r in rows:
    print(f"  invoice={r[0]} | status={r[1]} | amount={r[4]} {r[5]}")
    print(f"           ip={r[2]} | time={r[3]}")

# 4. validation_errors data
print("\n" + "=" * 55)
print("   TABLE: fastapi.validation_errors")
print("=" * 55)
cur.execute("SELECT error_code, field_name, rejected_at, LEFT(error_message, 80) FROM fastapi.validation_errors ORDER BY rejected_at DESC;")
rows = cur.fetchall()
print(f"Total rows: {len(rows)}")
for r in rows:
    print(f"  code={r[0]} | field={r[1]} | time={r[2]}")
    print(f"  reason={r[3]}...")

conn.close()
print("\nDone.")
