"""
One-time script to populate the service_list table in the database.
Run this ONCE after the new code is set up.

After this, you manage services from pgAdmin directly:
  - Add a new row    → fetcher starts pulling that service
  - Delete a row     → fetcher stops pulling that service
  - Set is_active=false → temporarily pause a service without deleting it
"""

from config_db import SessionLocal, ServiceList

# All the services we were previously fetching (moved from code → database)
INITIAL_SERVICES = [
    # (service_name,                endpoint,                                                      delta_column)
    ("vendor_master",               "/API_BUSINESS_PARTNER/A_Supplier",                             None),
    ("vendor_master_addr",          "/API_BUSINESS_PARTNER/A_BusinessPartnerAddress",               None),
    ("sale_order",                  "/API_SALES_ORDER_SRV/A_SalesOrder",                            "LastChangeDateTime"),
    ("sale_order_lines",            "/API_SALES_ORDER_SRV/A_SalesOrderItem",                        "LastChangeDateTime"),
    ("product_master",              "/API_PRODUCT_SRV/A_Product",                                   "LastChangeDateTime"),
    ("uom_master",                  "/API_PRODUCT_SRV/A_ProductUoM",                                None),
    ("status_code_master",          "/API_SALES_ORDER_SRV/A_SalesOrderStatus",                      None),
    ("sales_invoice",               "/API_BILLING_DOCUMENT_SRV/A_BillingDocument",                  "LastChangeDateTime"),
    ("sales_invoice_lines",         "/API_BILLING_DOCUMENT_SRV/A_BillingDocumentItem",              None),
    ("sales_order_hybrid",          "/API_SALES_ORDER_SRV/A_SalesOrder",                            "LastChangeDateTime"),
    ("purchase_order_hybrid",       "/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder",               "LastChangeDateTime"),
    ("sales_order_item",            "/API_SALES_ORDER_SRV/A_SalesOrderItem",                        "LastChangeDateTime"),
    ("purchase_order_item",         "/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrderItem",           None),
    ("sales_order_schedule",        "/API_SALES_ORDER_SRV/A_SalesOrderScheduleLine",                None),
    ("sales_order_partner",         "/API_SALES_ORDER_SRV/A_SalesOrderHeaderPartner",               None),
    ("po_schedule_line",            "/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrderScheduleLine",   None),
    ("po_pricing",                  "/API_PURCHASEORDER_PROCESS_SRV/A_PurOrdPricingElement",        None),
    ("sales_item_partner",          "/API_SALES_ORDER_SRV/A_SalesOrderItemPartner",                 None),
    ("sales_item_pricing",          "/API_SALES_ORDER_SRV/A_SalesOrderItemPrElement",               None),
    ("sales_order_hdr_pricing",     "/API_SALES_ORDER_SRV/A_SalesOrderHeaderPrElement",             None),
    ("sales_order_texts",           "/API_SALES_ORDER_SRV/A_SalesOrderText",                        None),
    ("sales_order_item_texts",      "/API_SALES_ORDER_SRV/A_SalesOrderItemText",                    None),
    ("po_account_assignment",       "/API_PURCHASEORDER_PROCESS_SRV/A_PurOrdAccountAssignment",     None),
    ("purchase_order_notes",        "/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrderNote",           None),
    ("po_item_notes",               "/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrderItemNote",       None),
]

def seed_services():
    """Insert all services into the database (skips if they already exist)."""
    with SessionLocal() as db:
        added = 0
        skipped = 0
        
        for name, endpoint, delta_col in INITIAL_SERVICES:
            # Check if this service already exists
            exists = db.query(ServiceList).filter_by(service_name=name).first()
            if exists:
                skipped += 1
                continue
            
            # Add new service
            new_service = ServiceList(
                service_name=name,
                endpoint=endpoint,
                delta_column=delta_col,
                is_active=True
            )
            db.add(new_service)
            added += 1
        
        db.commit()
        print(f"\nDone! Added {added} services, skipped {skipped} (already existed).")
        print(f"Total services in database: {added + skipped}")
        print(f"\nYou can now manage services from pgAdmin:")
        print(f"  → Open table: hybrid_orm.service_list")
        print(f"  → Add/remove/edit rows as needed\n")

if __name__ == "__main__":
    seed_services()
