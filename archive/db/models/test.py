from sqlalchemy import Column, Integer, String, DateTime, func
from db.base import Base

class User(Base):
    """User Model as shown in Senior's demonstration"""
    __tablename__ = "users"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(150), nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

class SyntheticData(Base):
    """Original Synthetic Data table"""
    __tablename__ = "synthetic_data"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    synthetic_value = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())

class AiVendor(Base):
    """Synthetic Vendor record matching SAP LFA1 for Pull/Push experiments"""
    __tablename__ = "ai_vendors"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), unique=True, nullable=False, comment="SAP Vendor Number Reference")
    NAME1 = Column(String(35), nullable=True)
    AI_Score = Column(Integer, nullable=True, comment="AI Generated Risk/Quality Score")
    AI_Classification = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime, default=func.now())

class AiInvoice(Base):
    """Synthetic Invoice record matching SAP RBKP for Pull/Push experiments"""
    __tablename__ = "ai_invoices"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False, comment="SAP Document Number Reference")
    GJAHR = Column(String(4), nullable=False, comment="SAP Fiscal Year Reference")
    LIFNR = Column(String(10), nullable=True)
    TotalAmount = Column(Integer, nullable=True)
    Anomalous = Column(Integer, default=0, comment="1 if AI detects anomaly")
    last_synced_at = Column(DateTime, default=func.now())

class SyncState(Base):
    """Sync State table as seen in pgAdmin"""
    __tablename__ = "_sync_state"
    __table_args__ = {"schema": "ai"}

    entity_name = Column(String(100), primary_key=True)
    last_sync_at = Column(DateTime, default=func.now())
    last_watermark = Column(String(100), nullable=True)
    records_synced = Column(Integer, default=0) # BIGINT in DB but Integer is safer for compat
    last_status = Column(String(20), default="SUCCESS")
    last_error = Column(String(255), nullable=True)
    total_syncs = Column(Integer, default=0)

class PromotedVendor(Base):
    """Promoted Vendor table in AI schema"""
    __tablename__ = "promoted_vendors"
    __table_args__ = {"schema": "ai"}

    vendor_id = Column(Integer, primary_key=True) # Manual ID as per DB
    sap_code = Column(String(30), nullable=False)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    street = Column(String(200), nullable=True)
    country_code = Column(String(10), nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(20), nullable=True)
    business_sector = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=func.now())
    created_by = Column(String(100), default="SYSTEM")
    _created_at = Column(DateTime, default=func.now())
    _updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PromotedInvoice(Base):
    """Promoted Invoice table in AI schema"""
    __tablename__ = "promoted_invoices"
    __table_args__ = {"schema": "ai"}

    invoice_number = Column(String(30), primary_key=True)
    fiscal_year = Column(Integer, primary_key=True) # INTEGER in DB
    vendor_code = Column(String(30), nullable=False)
    total_amount = Column(Integer, nullable=False) # NUMERIC(15,2) in DB, using Integer/Float
    currency = Column(String(10), default="INR")
    invoice_date = Column(DateTime, nullable=False)
    posting_date = Column(DateTime, nullable=False)
    _created_at = Column(DateTime, default=func.now())
    _updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PromotedInventory(Base):
    """Promoted Inventory table in AI schema"""
    __tablename__ = "promoted_inventory"
    __table_args__ = {"schema": "ai"}

    doc_number = Column(String(30), primary_key=True)
    doc_year = Column(Integer, primary_key=True) # INTEGER in DB
    item_number = Column(Integer, primary_key=True) # INTEGER in DB
    movement_type = Column(String(10), nullable=True)
    material_number = Column(String(40), nullable=False)
    plant = Column(String(10), nullable=True)
    storage_location = Column(String(10), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(10), nullable=True)
    _created_at = Column(DateTime, default=func.now())
    _updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PromotedPurchaseOrder(Base):
    """Promoted Purchase Order table in AI schema"""
    __tablename__ = "promoted_purchase_orders"
    __table_args__ = {"schema": "ai"}

    po_number = Column(String(30), primary_key=True)
    item_number = Column(Integer, primary_key=True) # INTEGER in DB
    vendor_code = Column(String(30), nullable=False)
    material_number = Column(String(40), nullable=False)
    description = Column(String(200), nullable=True)
    quantity = Column(Integer, nullable=False)
    net_price = Column(Integer, nullable=False)
    po_date = Column(DateTime, nullable=False)
    created_by = Column(String(100), default="PURCHASER")
    _created_at = Column(DateTime, default=func.now())
    _updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
