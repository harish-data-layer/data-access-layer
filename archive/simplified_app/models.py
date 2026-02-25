# MASTER MODELS FILE: All SAP and AI Blueprints in one place
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, ForeignKey, text
from sqlalchemy.orm import relationship, declarative_base

# Base class for all models
Base = declarative_base()

# --- SAP SCHEMA TABLES ---

class LFA1(Base):
    """Vendor Master Data"""
    __tablename__ = "lfa1"
    __table_args__ = {"schema": "sap"}
    id = Column(Integer, primary_key=True)
    LIFNR = Column(String(10), unique=True, nullable=False)
    NAME1 = Column(String(100))
    COUNTRY = Column(String(3))
    ERDAT = Column(Date)

class EKKO(Base):
    """Purchase Order Header"""
    __tablename__ = "ekko"
    __table_args__ = {"schema": "sap"}
    id = Column(Integer, primary_key=True)
    EBELN = Column(String(10), unique=True, nullable=False)
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"))
    BEDAT = Column(Date)
    BUKRS = Column(String(4))
    line_items = relationship("EKPO", backref="header")

class EKPO(Base):
    """Purchase Order Items"""
    __tablename__ = "ekpo"
    __table_args__ = {"schema": "sap"}
    id = Column(Integer, primary_key=True)
    EBELN = Column(String(10), ForeignKey("sap.ekko.EBELN"))
    MATNR = Column(String(18))
    MENGE = Column(Float)
    NETPR = Column(Float)

class RBKP(Base):
    """Invoice Header"""
    __tablename__ = "rbkp"
    __table_args__ = {"schema": "sap"}
    id = Column(Integer, primary_key=True)
    BELNR = Column(String(10), unique=True, nullable=False)
    GJAHR = Column(String(4))
    LIFNR = Column(String(10), ForeignKey("sap.lfa1.LIFNR"))
    RMWWR = Column(Float)
    BUKRS = Column(String(4))

# --- AI SCHEMA TABLES ---

class AiVendor(Base):
    """Enriched Vendor Data"""
    __tablename__ = "ai_vendors"
    __table_args__ = {"schema": "ai"}
    id = Column(Integer, primary_key=True)
    LIFNR = Column(String(10), unique=True)
    NAME1 = Column(String(100))
    AI_Score = Column(Integer)
    AI_Classification = Column(String(50))
    last_synced_at = Column(DateTime)

class AiInvoice(Base):
    """Enriched Invoice Data"""
    __tablename__ = "ai_invoices"
    __table_args__ = {"schema": "ai"}
    id = Column(Integer, primary_key=True)
    BELNR = Column(String(10))
    GJAHR = Column(String(4))
    LIFNR = Column(String(10))
    TotalAmount = Column(Integer)
    Anomalous = Column(Integer)
    last_synced_at = Column(DateTime)
