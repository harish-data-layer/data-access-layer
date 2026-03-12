import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Float, Boolean, func, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────────────────────────────
# DATABASE CONNECTION SETTINGS
# These values come from the .env file in the project root
# ─────────────────────────────────────────────────────────────────
DB_USER = os.getenv("DB_USER")
DB_PASS = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", ""))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

from sqlalchemy.pool import NullPool
engine = create_engine(
    DB_URL, 
    poolclass=NullPool,
    connect_args={
        "sslmode": "prefer",
        "connect_timeout": 30,
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─────────────────────────────────────────────────────────────────
# TABLE 1: sap_data  (Where fetched SAP records are stored)
# ─────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

class SapData(Base):
    """
    This table stores the actual data fetched from SAP.
    Each row = one service (e.g. 'vendor_master', 'sale_order')
    """
    __tablename__ = "sap_data"
    __table_args__ = {"schema": "hybrid_orm"}
    
    id                  = Column(Integer, primary_key=True, index=True)
    service_name        = Column(String(100), nullable=False, index=True)
    endpoint            = Column(String(500))
    record_count        = Column(Integer, default=0)
    payload             = Column(JSON, nullable=False)          # The actual SAP records
    last_data_timestamp = Column(DateTime(timezone=True))       # Newest record date from SAP
    last_sync           = Column(DateTime(timezone=True), server_default=func.now())  # When we last ran the fetch
    time_taken_seconds  = Column(Float, default=0)              # How many seconds the fetch took
    freshpull           = Column(Integer, default=0)            # How many new records pulled in the latest run


# ─────────────────────────────────────────────────────────────────
# TABLE 2: service_list  (Which services to fetch from SAP)
#
# Instead of hardcoding the list in the code, we store it here.
# You can add/remove/edit services directly in pgAdmin,
# and the code will automatically pick up the changes.
# ─────────────────────────────────────────────────────────────────
class ServiceList(Base):
    """
    This table is your 'remote control' for the SAP fetcher.
    Add a row here = fetcher will start pulling that service.
    Delete a row   = fetcher will stop pulling that service.
    """
    __tablename__ = "service_list"
    __table_args__ = {"schema": "hybrid_orm"}
    
    id              = Column(Integer, primary_key=True, index=True)
    service_name    = Column(String(100), unique=True, nullable=False, index=True)
    endpoint        = Column(String(500), nullable=False)
    delta_column    = Column(String(100), nullable=True)   # Column name for fetching only new data (optional)
    is_active       = Column(Boolean, default=True)        # Toggle ON/OFF without deleting


# ─────────────────────────────────────────────────────────────────
# AUTO-SETUP: Create schema and tables if they don't exist
# ─────────────────────────────────────────────────────────────────
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS hybrid_orm"))
    conn.commit()

Base.metadata.create_all(bind=engine)

# Migration: Add time_taken_seconds column if it doesn't exist yet
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE hybrid_orm.sap_data ADD COLUMN time_taken_seconds FLOAT"))
        conn.commit()
        print("[DB SETUP] Added column: time_taken_seconds")
    except Exception:
        conn.rollback()

# Migration: Add freshpull column if it doesn't exist yet
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE hybrid_orm.sap_data ADD COLUMN freshpull INTEGER DEFAULT 0"))
        conn.commit()
        print("[DB SETUP] Added column: freshpull")
    except Exception:
        conn.rollback()

# Migration: Drop vector_embeddings column if it still exists in old table
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE hybrid_orm.hybrid_orm DROP COLUMN IF EXISTS vector_embeddings"))
        conn.commit()
        print("[DB SETUP] Removed old column: vector_embeddings")
    except Exception:
        conn.rollback()
