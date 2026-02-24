from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=2,
    max_overflow=0
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define schemas
SCHEMAS = [
    "semantic_layer",
    "curated_layer",
    "integration_layer",
    "dq_layer",
    "vector_layer",
    "event_store",
    "audit_layer",
    "push_layer",
    "sap",
    "ai"
]

class Base(DeclarativeBase):
    pass
