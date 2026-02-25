#!/usr/bin/env python3
import sys
from logger import get_logger
from sync_materials import pull_sap_to_postgres, push_postgres_to_sap

log = get_logger("MAIN")

def main():
    args = sys.argv[1:]
    if not args:
        print("""
SAP ↔ PostgreSQL Sync Pipeline
-------------------------------
USAGE:
  python main.py pull              → Pull all materials
  python main.py pull FERT         → Pull only FERT type
  python main.py push              → Push all records from PG to SAP
  python main.py push MAT001       → Push specific material
""")
        return

    action = args[0].lower()
    param  = args[1] if len(args) > 1 else None

    if action == "pull":
        count = pull_sap_to_postgres(product_type=param)
        log.info(f"DONE: {count} records synced to PostgreSQL.")
    elif action == "push":
        count = push_postgres_to_sap(product_id=param)
        log.info(f"DONE: {count} records pushed to SAP.")
    else:
        log.error(f"Unknown action: {action}")

if __name__ == "__main__":
    main()
