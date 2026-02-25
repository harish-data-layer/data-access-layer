from sqlalchemy import Column, String, DateTime, func, JSON, Float
from db.base import Base
import uuid

class DataAccessLog(Base):
    __tablename__ = "data_access_logs"
    __table_args__ = {"schema": "audit_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entityName = Column(String, nullable=False)
    recordId = Column(String, nullable=True)
    operation = Column(String, nullable=False)
    accessedBy = Column(String, nullable=False)
    accessedByType = Column(String, nullable=False)
    accessedAt = Column(DateTime, default=func.now())

class DataChangeLog(Base):
    __tablename__ = "data_change_logs"
    __table_args__ = {"schema": "audit_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entityName = Column(String, nullable=False)
    recordId = Column(String, nullable=False)
    operation = Column(String, nullable=False)
    oldValue = Column(JSON, nullable=True)
    newValue = Column(JSON, nullable=True)
    changedBy = Column(String, nullable=False)
    changedByType = Column(String, nullable=False)
    changedAt = Column(DateTime, default=func.now())

class AiActionLog(Base):
    __tablename__ = "ai_action_logs"
    __table_args__ = {"schema": "audit_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actionId = Column(String, unique=True, nullable=False)
    agentName = Column(String, nullable=False)
    actionType = Column(String, nullable=False)
    entityName = Column(String, nullable=False)
    recordId = Column(String, nullable=True)
    inputData = Column(JSON, nullable=True)
    outputData = Column(JSON, nullable=True)
    confidenceScore = Column(Float, nullable=True)
    reasoning = Column(String, nullable=True)
    executedAt = Column(DateTime, default=func.now())
