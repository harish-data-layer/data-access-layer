import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ==============================================================================
# 1. Load the secret passwords from .env file
# ==============================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ==============================================================================
# 2. Create the Database Link (URL) safely
# ==============================================================================
# Safely grab the database password (handles special characters like @ or #)
safe_password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", ""))
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{safe_password}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"

# ==============================================================================
# 3. Set up SQLAlchemy
# ==============================================================================
# Engine tells SQLAlchemy how to talk to PostgreSQL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory that gives us a new database connection when we ask
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our future tables will inherit from
Base = declarative_base()

# ==============================================================================
# 4. Connection Helper for FastAPI
# ==============================================================================
def get_db():
    """Gives us a new database connection, and closes it when we are done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
