from sqlalchemy import Column, String, Integer, DateTime, func, JSON
from db.base import Base
import uuid

class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "event_store"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    eventId = Column(String, unique=True, nullable=False)
    eventType = Column(String, nullable=False)
    aggregateId = Column(String, nullable=False)
    aggregateType = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True) # metadata is reserved in SQLAlchemy
    correlationId = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    version = Column(Integer, default=1)
