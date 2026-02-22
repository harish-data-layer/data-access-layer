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
