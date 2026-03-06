from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from sqlalchemy import text
from .database import Base, engine

# ==============================================================================
# 1. Define the Database Table (The Schema)
# ==============================================================================
# We use a JSON column for 'payload' because SAP data structure changes a lot.
class SapExtraction(Base):
    __tablename__ = "sap_sync_data"
    __table_args__ = {"schema": "sap_sap"}  # Tells Postgres to put this inside the 'sap_sap' folder

    id = Column(Integer, primary_key=True)
    entity_name = Column(String, unique=True, index=True) # Example: 'A_SalesOrder'
    payload = Column(JSON)  # Stores the entire list of SAP records inside one row
    last_sync = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ==============================================================================
# 2. Auto-Create Tables on Startup
# ==============================================================================
# This connects to Postgres, makes sure the 'sap_sap' schema folder exists, then creates the table safely.
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS sap_sap;"))
    conn.commit()

# Actively create the table now
Base.metadata.create_all(bind=engine)
