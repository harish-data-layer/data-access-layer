from sqlalchemy import Column, String, Integer, DateTime, func, JSON
from db.base import Base
import uuid

class PushQueue(Base):
    __tablename__ = "push_queue"
    __table_args__ = {"schema": "push_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    queueId = Column(String, unique=True, nullable=False)
    targetSystem = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    operation = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    priority = Column(Integer, default=5)
    retryCount = Column(Integer, default=0)
    maxRetries = Column(Integer, default=3)
    createdAt = Column(DateTime, default=func.now())
    processedAt = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)
