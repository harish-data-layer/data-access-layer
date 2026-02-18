from sqlalchemy import Column, String, Boolean, DateTime, func, JSON
from db.base import Base
import uuid

class BusinessRule(Base):
    __tablename__ = "business_rules"
    __table_args__ = {"schema": "semantic_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ruleId = Column(String, unique=True, nullable=False)
    ruleName = Column(String, nullable=False)
    entityName = Column(String, nullable=False)
    ruleType = Column(String, nullable=False)
    sqlExpression = Column(String, nullable=True)
    jsonSchema = Column(JSON, nullable=True)
    aiExplanation = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    isActive = Column(Boolean, default=True)
    createdBy = Column(String, nullable=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
