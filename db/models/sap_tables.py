"""
SAP Tables - SQLAlchemy Models with FK relationships
Schema: sap_layer
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base


class LFA1(Base):
    """Vendor Master Data"""
    __tablename__ = "lfa1"
    __table_args__ = {"schema": "sap_layer"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), nullable=False, unique=True, comment="Vendor Number")
    NAME1 = Column(String(35), nullable=True, comment="Vendor Name")
    LAND1 = Column(String(3), nullable=True, comment="Country Key")
    STCD1 = Column(String(16), nullable=True, comment="Tax Number 1 (GST/VAT)")
    KTOKK = Column(String(4), nullable=True, comment="Vendor Account Group")
    created_at = Column(DateTime, default=func.now())

    company_codes = relationship("LFB1", back_populates="vendor")
    purchase_orders = relationship("EKKO", back_populates="vendor")
    invoices = relationship("RBKP", back_populates="vendor")


class LFB1(Base):
    """Vendor Company Code Data"""
    __tablename__ = "lfb1"
    __table_args__ = (
        UniqueConstraint("LIFNR", "BUKRS", name="lfb1_lifnr_bukrs_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), ForeignKey("sap_layer.lfa1.LIFNR"), nullable=False, comment="Vendor Number")
    BUKRS = Column(String(4), nullable=False, comment="Company Code")
    AKONT = Column(String(10), nullable=True, comment="Reconciliation Account")
    ZTERM = Column(String(4), nullable=True, comment="Payment Terms Key")
    created_at = Column(DateTime, default=func.now())

    vendor = relationship("LFA1", back_populates="company_codes")


class EKKO(Base):
    """Purchase Order Header"""
    __tablename__ = "ekko"
    __table_args__ = {"schema": "sap_layer"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    EBELN = Column(String(10), nullable=False, unique=True, comment="Purchase Order Number")
    BUKRS = Column(String(4), nullable=True, comment="Company Code")
    LIFNR = Column(String(10), ForeignKey("sap_layer.lfa1.LIFNR"), nullable=True, comment="Vendor Number")
    BEDAT = Column(Date, nullable=True, comment="Purchase Order Date")
    WAERS = Column(String(5), nullable=True, comment="Currency Key")
    NETWR = Column(Float, nullable=True, comment="Net Order Value")
    created_at = Column(DateTime, default=func.now())

    vendor = relationship("LFA1", back_populates="purchase_orders")
    line_items = relationship("EKPO", back_populates="po_header")


class EKPO(Base):
    """Purchase Order Line Items"""
    __tablename__ = "ekpo"
    __table_args__ = (
        UniqueConstraint("EBELN", "EBELP", name="ekpo_ebeln_ebelp_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    EBELN = Column(String(10), ForeignKey("sap_layer.ekko.EBELN"), nullable=False, comment="Purchase Order Number")
    EBELP = Column(String(5), nullable=False, comment="PO Item Number")
    MATNR = Column(String(18), nullable=True, comment="Material Number")
    MENGE = Column(Float, nullable=True, comment="Purchase Order Quantity")
    MEINS = Column(String(3), nullable=True, comment="Unit of Measure")
    NETPR = Column(Float, nullable=True, comment="Net Price")
    NETWR = Column(Float, nullable=True, comment="Net Order Value")
    created_at = Column(DateTime, default=func.now())

    po_header = relationship("EKKO", back_populates="line_items")


class RBKP(Base):
    """Invoice Document Header"""
    __tablename__ = "rbkp"
    __table_args__ = (
        UniqueConstraint("BELNR", "GJAHR", name="rbkp_belnr_gjahr_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False, comment="Document Number")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BLDAT = Column(Date, nullable=True, comment="Document Date")
    BUDAT = Column(Date, nullable=True, comment="Posting Date")
    LIFNR = Column(String(10), ForeignKey("sap_layer.lfa1.LIFNR"), nullable=True, comment="Vendor Number")
    XBLNR = Column(String(16), nullable=True, comment="Reference Document Number")
    WAERS = Column(String(5), nullable=True, comment="Currency Key")
    RMWWR = Column(Float, nullable=True, comment="Gross Invoice Amount")
    created_at = Column(DateTime, default=func.now())

    vendor = relationship("LFA1", back_populates="invoices")
    line_items = relationship("RSEG", back_populates="invoice_header",
                              foreign_keys="[RSEG.BELNR, RSEG.GJAHR]",
                              primaryjoin="and_(RBKP.BELNR == foreign(RSEG.BELNR), RBKP.GJAHR == foreign(RSEG.GJAHR))")


class RSEG(Base):
    """Invoice Document Line Items"""
    __tablename__ = "rseg"
    __table_args__ = (
        UniqueConstraint("BELNR", "GJAHR", "BUZEI", name="rseg_belnr_gjahr_buzei_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False, comment="Invoice Document Number")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BUZEI = Column(String(3), nullable=False, comment="Line Item Number")
    EBELN = Column(String(10), nullable=True, comment="Purchase Order Number")
    EBELP = Column(String(5), nullable=True, comment="PO Item Number")
    MATNR = Column(String(18), nullable=True, comment="Material Number")
    MENGE = Column(Float, nullable=True, comment="Quantity")
    WRBTR = Column(Float, nullable=True, comment="Amount in Document Currency")
    BWTAR = Column(String(10), nullable=True, comment="Valuation Type")
    created_at = Column(DateTime, default=func.now())

    invoice_header = relationship("RBKP", back_populates="line_items",
                                  foreign_keys=[BELNR, GJAHR],
                                  primaryjoin="and_(RSEG.BELNR == RBKP.BELNR, RSEG.GJAHR == RBKP.GJAHR)")


class BKPF(Base):
    """Accounting Document Header"""
    __tablename__ = "bkpf"
    __table_args__ = (
        UniqueConstraint("BUKRS", "BELNR", "GJAHR", name="bkpf_bukrs_belnr_gjahr_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BUKRS = Column(String(4), nullable=False, comment="Company Code")
    BELNR = Column(String(10), nullable=False, comment="Accounting Document Number")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BLART = Column(String(2), nullable=True, comment="Document Type")
    BUDAT = Column(Date, nullable=True, comment="Posting Date")
    CPUDT = Column(Date, nullable=True, comment="Entry Date")
    USNAM = Column(String(12), nullable=True, comment="User Name")
    created_at = Column(DateTime, default=func.now())

    line_items = relationship("BSEG", back_populates="doc_header",
                              foreign_keys="[BSEG.BUKRS, BSEG.BELNR, BSEG.GJAHR]",
                              primaryjoin="and_(BKPF.BUKRS == foreign(BSEG.BUKRS), BKPF.BELNR == foreign(BSEG.BELNR), BKPF.GJAHR == foreign(BSEG.GJAHR))")


class BSEG(Base):
    """Accounting Document Segment"""
    __tablename__ = "bseg"
    __table_args__ = (
        UniqueConstraint("BUKRS", "BELNR", "GJAHR", "BUZEI", name="bseg_keys_unique"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BUKRS = Column(String(4), nullable=False, comment="Company Code")
    BELNR = Column(String(10), nullable=False, comment="Accounting Document Number")
    GJAHR = Column(String(4), nullable=False, comment="Fiscal Year")
    BUZEI = Column(String(3), nullable=False, comment="Line Item Number")
    KOART = Column(String(1), nullable=True, comment="Account Type")
    SHKZG = Column(String(1), nullable=True, comment="Debit/Credit Indicator")
    WRBTR = Column(Float, nullable=True, comment="Amount in Document Currency")
    DMBTR = Column(Float, nullable=True, comment="Amount in Local Currency")
    HKONT = Column(String(10), nullable=True, comment="General Ledger Account")
    KOSTL = Column(String(10), nullable=True, comment="Cost Center")
    created_at = Column(DateTime, default=func.now())

    doc_header = relationship("BKPF", back_populates="line_items",
                              foreign_keys=[BUKRS, BELNR, GJAHR],
                              primaryjoin="and_(BSEG.BUKRS == BKPF.BUKRS, BSEG.BELNR == BKPF.BELNR, BSEG.GJAHR == BKPF.GJAHR)")


class MKPF(Base):
    """Material Document Header"""
    __tablename__ = "mkpf"
    __table_args__ = (
        UniqueConstraint("MBLNR", "MJAHR", name="mkpf_mblnr_mjahr_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    MBLNR = Column(String(10), nullable=False, comment="Material Document Number")
    MJAHR = Column(String(4), nullable=False, comment="Material Document Year")
    BLDAT = Column(Date, nullable=True, comment="Document Date")
    BUDAT = Column(Date, nullable=True, comment="Posting Date")
    USNAM = Column(String(12), nullable=True, comment="User Name")
    created_at = Column(DateTime, default=func.now())

    line_items = relationship("MSEG", back_populates="mat_doc_header",
                              foreign_keys="[MSEG.MBLNR, MSEG.MJAHR]",
                              primaryjoin="and_(MKPF.MBLNR == foreign(MSEG.MBLNR), MKPF.MJAHR == foreign(MSEG.MJAHR))")


class MSEG(Base):
    """Material Document Line Items"""
    __tablename__ = "mseg"
    __table_args__ = (
        UniqueConstraint("MBLNR", "MJAHR", "ZEILE", name="mseg_mblnr_mjahr_zeile_key"),
        {"schema": "sap_layer"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    MBLNR = Column(String(10), nullable=False, comment="Material Document Number")
    MJAHR = Column(String(4), nullable=False, comment="Material Document Year")
    ZEILE = Column(String(4), nullable=False, comment="Line Item in Material Document")
    MATNR = Column(String(18), nullable=True, comment="Material Number")
    WERKS = Column(String(4), nullable=True, comment="Plant")
    MENGE = Column(Float, nullable=True, comment="Quantity")
    MEINS = Column(String(3), nullable=True, comment="Unit of Measure")
    EBELN = Column(String(10), nullable=True, comment="Purchase Order Number")
    EBELP = Column(String(5), nullable=True, comment="PO Item Number")
    created_at = Column(DateTime, default=func.now())

    mat_doc_header = relationship("MKPF", back_populates="line_items",
                                  foreign_keys=[MBLNR, MJAHR],
                                  primaryjoin="and_(MSEG.MBLNR == MKPF.MBLNR, MSEG.MJAHR == MKPF.MJAHR)")
