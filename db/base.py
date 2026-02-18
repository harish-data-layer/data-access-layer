from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
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
    "push_layer"
]

class Base(DeclarativeBase):
    pass
