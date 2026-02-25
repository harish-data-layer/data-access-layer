"""
SAP Tables - SQLAlchemy Models for Synthetic Data Seeding
Schema: sap
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, func, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from db.base import Base

class LFA1(Base):
    """Vendor Master Data"""
    __tablename__ = "lfa1"
    __table_args__ = {"schema": "sap"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), nullable=False, unique=True)
    NAME1 = Column(String(35))
    COUNTRY = Column(String(3))
    ERDAT = Column(Date)
    
    company_codes = relationship("LFB1", back_populates="vendor")
    purchase_orders = relationship("EKKO", back_populates="vendor")
    invoices = relationship("RBKP", back_populates="vendor")

class LFB1(Base):
    """Vendor Master (Company Code)"""
    __tablename__ = "lfb1"
    __table_args__ = (
        UniqueConstraint("LIFNR", "BUKRS", name="lfb1_lifnr_bukrs_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"), nullable=False)
    BUKRS = Column(String(4), nullable=False)
    ERDAT = Column(Date)
    
    vendor = relationship("LFA1", back_populates="company_codes")

class EKKO(Base):
    """Purchasing Document Header"""
    __tablename__ = "ekko"
    __table_args__ = {"schema": "sap"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    EBELN = Column(String(10), nullable=False, unique=True)
    BUKRS = Column(String(4))
    AEDAT = Column(Date)
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"))
    WAERS = Column(String(5))
    NETWR = Column(Float)

    vendor = relationship("LFA1", back_populates="purchase_orders")
    line_items = relationship("EKPO", back_populates="po_header")

class EKPO(Base):
    """Purchasing Document Item"""
    __tablename__ = "ekpo"
    __table_args__ = (
        UniqueConstraint("EBELN", "EBELP", name="ekpo_ebeln_ebelp_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    EBELN = Column(String(10), ForeignKey("sap.ekko.EBELN"), nullable=False)
    EBELP = Column(String(5), nullable=False)
    MATNR = Column(String(18))
    MENGE = Column(Float)
    NETPR = Column(Float)
    NETWR = Column(Float)

    po_header = relationship("EKKO", back_populates="line_items")

class RBKP(Base):
    """Document Header: Invoice Receipt"""
    __tablename__ = "rbkp"
    __table_args__ = (
        UniqueConstraint("BELNR", "GJAHR", name="rbkp_belnr_gjahr_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False)
    GJAHR = Column(String(4), nullable=False)
    BLDAT = Column(Date)
    BUDAT = Column(Date)
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"))
    BUKRS = Column(String(4))
    RMWWR = Column(Float)

    vendor = relationship("LFA1", back_populates="invoices")
    line_items = relationship("RSEG", back_populates="invoice_header",
                               primaryjoin="and_(RBKP.BELNR == RSEG.BELNR, RBKP.GJAHR == RSEG.GJAHR)",
                               foreign_keys="[RSEG.BELNR, RSEG.GJAHR]")

class RSEG(Base):
    """Document Item: Incoming Invoice"""
    __tablename__ = "rseg"
    __table_args__ = (
        UniqueConstraint("BELNR", "GJAHR", "BUZEI", name="rseg_belnr_gjahr_buzei_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BELNR = Column(String(10), nullable=False)
    GJAHR = Column(String(4), nullable=False)
    BUZEI = Column(String(6), nullable=False)
    EBELN = Column(String(10))
    EBELP = Column(String(5))
    WRBTR = Column(Float)
    MENGE = Column(Float)

    invoice_header = relationship("RBKP", back_populates="line_items",
                                  primaryjoin="and_(RSEG.BELNR == RBKP.BELNR, RSEG.GJAHR == RBKP.GJAHR)",
                                  foreign_keys="[RSEG.BELNR, RSEG.GJAHR]")

class BKPF(Base):
    """Accounting Document Header"""
    __tablename__ = "bkpf"
    __table_args__ = (
        UniqueConstraint("BUKRS", "BELNR", "GJAHR", name="bkpf_bukrs_belnr_gjahr_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BUKRS = Column(String(4), nullable=False)
    BELNR = Column(String(10), nullable=False)
    GJAHR = Column(String(4), nullable=False)
    BLDAT = Column(Date)
    BUDAT = Column(Date)
    WAERS = Column(String(5))

    line_items = relationship("BSEG", back_populates="doc_header",
                               primaryjoin="and_(BKPF.BUKRS == BSEG.BUKRS, BKPF.BELNR == BSEG.BELNR, BKPF.GJAHR == BSEG.GJAHR)",
                               foreign_keys="[BSEG.BUKRS, BSEG.BELNR, BSEG.GJAHR]")

class BSEG(Base):
    """Accounting Document Segment"""
    __tablename__ = "bseg"
    __table_args__ = (
        UniqueConstraint("BUKRS", "BELNR", "GJAHR", "BUZEI", name="bseg_keys_unique"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    BUKRS = Column(String(4), nullable=False)
    BELNR = Column(String(10), nullable=False)
    GJAHR = Column(String(4), nullable=False)
    BUZEI = Column(String(3), nullable=False)
    DMBTR = Column(Float)
    WRBTR = Column(Float)
    LIFNR = Column(String(10))

    doc_header = relationship("BKPF", back_populates="line_items",
                                primaryjoin="and_(BSEG.BUKRS == BKPF.BUKRS, BSEG.BELNR == BKPF.BELNR, BSEG.GJAHR == BKPF.GJAHR)",
                                foreign_keys="[BSEG.BUKRS, BSEG.BELNR, BSEG.GJAHR]")

class MKPF(Base):
    """Header: Material Document"""
    __tablename__ = "mkpf"
    __table_args__ = (
        UniqueConstraint("MBLNR", "MJAHR", name="mkpf_mblnr_mjahr_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    MBLNR = Column(String(10), nullable=False)
    MJAHR = Column(String(4), nullable=False)
    BLDAT = Column(Date)
    BUDAT = Column(Date)
    USNAM = Column(String(12))

    line_items = relationship("MSEG", back_populates="mat_doc_header",
                              primaryjoin="and_(MKPF.MBLNR == MSEG.MBLNR, MKPF.MJAHR == MSEG.MJAHR)",
                              foreign_keys="[MSEG.MBLNR, MSEG.MJAHR]")

class MSEG(Base):
    """Document Segment: Material"""
    __tablename__ = "mseg"
    __table_args__ = (
        UniqueConstraint("MBLNR", "MJAHR", "ZEILE", name="mseg_mblnr_mjahr_zeile_key"),
        {"schema": "sap"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    MBLNR = Column(String(10), nullable=False)
    MJAHR = Column(String(4), nullable=False)
    ZEILE = Column(String(4), nullable=False)
    BWART = Column(String(3))
    MATNR = Column(String(18))
    MENGE = Column(Float)
    LIFNR = Column(String(10))

    mat_doc_header = relationship("MKPF", back_populates="line_items",
                                   primaryjoin="and_(MSEG.MBLNR == MKPF.MBLNR, MSEG.MJAHR == MKPF.MJAHR)",
                                   foreign_keys="[MSEG.MBLNR, MSEG.MJAHR]")
