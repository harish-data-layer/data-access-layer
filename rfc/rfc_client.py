#!/usr/bin/env python3
# =============================================================
#  rfc_client.py - SAP RFC Connection Client
#
#  Uses Anna's connection: /H/s1.mncinfosys.com/S/3240
#  Calls RFC_READ_TABLE to fetch ANY SAP table
#
#  Much faster than GUI scripting:
#    GUI:  ~1 min per 200 rows (cell by cell)
#    RFC:  ~5 sec for 50,000 rows (bulk transfer)
# =============================================================

import sys
import logging
from config import SAP_RFC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rfc.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("RFC")


class SAPRFCClient:
    """
    SAP RFC Client using pyrfc library.

    How RFC works:
        Your PC  -->  RFC/TCP port 3240  -->  SAP Application Server
                                                     |
                                              RFC_READ_TABLE
                                              (reads any DB table)
                                                     |
                                              Returns rows as text

    Usage:
        client = SAPRFCClient()
        rows = client.read_table("MARA", max_rows=10000)
        rows = client.read_table("LFA1", fields=["LIFNR","NAME1","LAND1"])
        rows = client.read_table("EKKO", where="BUKRS = '1000'")
    """

    def __init__(self):
        self.conn = None
        self._connect()

    def _connect(self):
        try:
            import pyrfc
        except ImportError:
            log.error("pyrfc not installed!")
            log.error("Install: pip install pyrfc")
            log.error("Also needs: SAP NW RFC SDK (nwrfcsdk)")
            log.error("Download from SAP portal: https://support.sap.com (search 'SAP NW RFC SDK')")
            raise

        log.info(f"Connecting to SAP via RFC: {SAP_RFC['ashost']}:{SAP_RFC['sysnr']}")
        try:
            self.conn = pyrfc.Connection(**SAP_RFC)
            log.info("RFC connection established successfully!")
        except Exception as e:
            log.error(f"RFC connection failed: {e}")
            raise

    def read_table(self, table_name, fields=None, where=None, max_rows=50000, delimiter="|"):
        """
        Read any SAP table using RFC_READ_TABLE function module.

        Args:
            table_name: SAP table name (e.g. 'MARA', 'LFA1', 'EKKO')
            fields:     List of field names to fetch. None = all fields.
            where:      WHERE clause string (e.g. "BUKRS = '1000'")
            max_rows:   Max rows to fetch (default 50000)
            delimiter:  Field separator in results (default '|')

        Returns:
            List of dicts [{"matnr": "MAT001", "mtart": "FERT", ...}, ...]

        How RFC_READ_TABLE works:
            - Connects to SAP application server via RFC
            - Calls the ABAP function module RFC_READ_TABLE
            - SAP queries the database table directly
            - Returns data as pipe-delimited text rows
            - We parse those back into dicts
        """
        log.info(f"Reading table: {table_name} (max {max_rows} rows)")

        # Prepare fields parameter
        fields_param = []
        if fields:
            fields_param = [{"FIELDNAME": f.upper()} for f in fields]

        # Prepare WHERE conditions
        options_param = []
        if where:
            # RFC_READ_TABLE WHERE clause must be chunked into 72-char strings
            for i in range(0, len(where), 72):
                options_param.append({"TEXT": where[i:i+72]})

        try:
            result = self.conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE = table_name.upper(),
                DELIMITER   = delimiter,
                NO_DATA     = "",
                ROWSKIPS    = 0,
                ROWCOUNT    = max_rows,
                FIELDS      = fields_param,
                OPTIONS     = options_param,
            )
        except Exception as e:
            log.error(f"RFC_READ_TABLE failed for {table_name}: {e}")
            raise

        # Parse field metadata
        field_meta = result.get("FIELDS", [])
        col_names  = [f["FIELDNAME"].lower() for f in field_meta]

        # Parse rows (each row is a pipe-delimited string)
        raw_rows = result.get("DATA", [])
        log.info(f"Raw rows received: {len(raw_rows)}, Columns: {len(col_names)}")

        records = []
        for raw in raw_rows:
            line = raw.get("WA", "")
            values = line.split(delimiter)

            # Pad if row has fewer values than columns
            while len(values) < len(col_names):
                values.append("")

            row = {}
            for i, col in enumerate(col_names):
                row[col] = values[i].strip() if i < len(values) else ""
            records.append(row)

        log.info(f"Parsed {len(records)} records from {table_name}")
        return records

    def call_fm(self, function_module, **kwargs):
        """
        Call any RFC function module directly.

        Example:
            result = client.call_fm("STFC_CONNECTION", REQUTEXT="Hello SAP")
            print(result)
        """
        return self.conn.call(function_module, **kwargs)

    def test_connection(self):
        """Quick ping to verify RFC connection is alive."""
        try:
            result = self.conn.call("STFC_CONNECTION", REQUTEXT="Ping")
            echo = result.get("ECHOTEXT", "")
            log.info(f"RFC ping successful! Echo: {echo}")
            return True
        except Exception as e:
            log.error(f"RFC ping failed: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            log.info("RFC connection closed.")


# =============================================================
#  QUICK TEST - Run directly to test RFC connectivity
# =============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("Testing SAP RFC connection...")
    print(f"Host  : {SAP_RFC['ashost']}")
    print(f"SysNr : {SAP_RFC['sysnr']}")
    print(f"Client: {SAP_RFC['client']}")
    print(f"User  : {SAP_RFC['user']}")
    print("=" * 55)

    try:
        client = SAPRFCClient()
        ok = client.test_connection()

        if ok:
            print("\nRFC connection WORKS!")
            print("Try pulling a table:")
            print("  python rfc_pull.py MARA")
            print("  python rfc_pull.py LFA1")

            # Show a quick sample
            print("\nFetching 5 rows from MARA...")
            rows = client.read_table("MARA",
                fields=["MATNR", "MTART", "MATKL", "MEINS"],
                max_rows=5)
            for r in rows:
                print(f"  {r}")

        client.close()

    except ImportError:
        print("\nMissing: pyrfc library")
        print("\nINSTALLATION STEPS:")
        print("1. Download SAP NW RFC SDK from SAP support portal")
        print("2. Extract to C:/nwrfcsdk/")
        print("3. Add C:/nwrfcsdk/lib to system PATH")
        print("4. pip install pyrfc")
    except Exception as e:
        print(f"\nRFC connection FAILED: {e}")
        print("Check: host, sysnr, client, user, password in config.py")
