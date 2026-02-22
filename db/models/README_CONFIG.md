# Database Configuration Map

To "configure" or "modify" a table, you simply edit the corresponding Python file in this directory.

## Which file controls which table?

| Table Name (in Database) | "Config" File (Edit this) | Description |
| :--- | :--- | :--- |
| **curated_vendors** | `curated_vendor.py` | Vendors, suppliers, GST info |
| **curated_invoices** | `curated_invoice.py` | Invoice details, amounts, dates |
| **entities** | `entity.py` | Semantic layer entities |
| **attributes** | `attribute.py` | Entity attributes |
| **business_rules** | `business_rule.py` | Validation and logic rules |
| **extraction_metadata** | `extraction_metadata.py` | Data ingestion status |
| **dq_scores** | `dq_score.py` | Data quality scores |
| **events** | `event.py` | System events |
| **audit_logs** | `audit_log.py` | Access and change logs |

## How to Edit?

1.  Open the file (e.g., `curated_vendor.py`).
2.  Add a new line inside the class:
    ```python
    phone_number = Column(String, nullable=True)
    ```
3.  Save the file.
4.  Run `update_schema "added phone number"` in your terminal.
