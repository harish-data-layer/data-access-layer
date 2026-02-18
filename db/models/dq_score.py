from sqlalchemy import Column, String, Float, DateTime, func
from db.base import Base
import uuid

class DqScore(Base):
    __tablename__ = "dq_scores"
    __table_args__ = {"schema": "dq_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entityName = Column(String, nullable=False)
    recordId = Column(String, nullable=True)
    completeness = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    consistency = Column(Float, nullable=True)
    validity = Column(Float, nullable=True)
    timeliness = Column(Float, nullable=True)
    uniqueness = Column(Float, nullable=True)
    compositeScore = Column(Float, nullable=False)
    measuredAt = Column(DateTime, default=func.now())
