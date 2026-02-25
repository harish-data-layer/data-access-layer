import psycopg2
import psycopg2.extras
from logger import get_logger
from config import POSTGRES, SYNC

log = get_logger("DB")

class PostgresDB:
    def __init__(self):
        self.conn = psycopg2.connect(
            host     = POSTGRES["host"],
            port     = POSTGRES["port"],
            dbname   = POSTGRES["database"],
            user     = POSTGRES["username"],
            password = POSTGRES["password"],
        )
        self.conn.autocommit = False
        log.info(f"PostgreSQL connected: {POSTGRES['host']}/{POSTGRES['database']}")
        self._ensure_schema()

    def _ensure_schema(self):
        with self.conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS sap;")
        self.conn.commit()
        log.info("Schema 'sap' verified.")

    def close(self):
        self.conn.close()
        log.info("PostgreSQL connection closed.")

    def create_table_if_not_exists(self, table: str, columns: dict):
        col_defs = ", ".join(f'"{k}" {v}' for k, v in columns.items())
        # Use sap schema prefix
        query = f'CREATE TABLE IF NOT EXISTS sap."{table}" ({col_defs});'
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()
        log.info(f"Table ready: sap.{table}")

    def upsert(self, table: str, records: list, primary_key: str):
        if not records:
            log.warning("No records to upsert.")
            return 0

        columns  = list(records[0].keys())
        col_str  = ", ".join(f'"{c}"' for c in columns)
        val_str  = ", ".join(f"%({c})s" for c in columns)
        update_str = ", ".join(
            f'"{c}" = EXCLUDED."{c}"' for c in columns if c != primary_key
        )

        query = f"""
            INSERT INTO sap."{table}" ({col_str})
            VALUES ({val_str})
            ON CONFLICT ("{primary_key}")
            DO UPDATE SET {update_str};
        """

        batch_size = SYNC["batch_size"]
        total = 0

        with self.conn.cursor() as cur:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                psycopg2.extras.execute_batch(cur, query, batch)
                self.conn.commit()
                total += len(batch)
                log.info(f"  Upserted batch {i//batch_size + 1}: {total}/{len(records)} rows")

        log.info(f"Upsert complete: {total} rows in sap.{table}")
        return total

    def read(self, table: str, where: str = None) -> list:
        query = f'SELECT * FROM sap."{table}"'
        if where:
            query += f" WHERE {where}"

        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        log.info(f"Read {len(rows)} rows from sap.{table}")
        return [dict(r) for r in rows]
