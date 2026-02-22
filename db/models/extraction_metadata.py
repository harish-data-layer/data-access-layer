from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey
from db.base import Base
import uuid

class ExtractionMetadata(Base):
    __tablename__ = "extraction_metadata"
    __table_args__ = {"schema": "integration_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    extractionId = Column(String, unique=True, nullable=False)
    source = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    extractionType = Column(String, nullable=False)
    status = Column(String, nullable=False)
    recordsExtracted = Column(Integer, default=0)
    recordsFailed = Column(Integer, default=0)
    startedAt = Column(DateTime, nullable=False)
    completedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=func.now())
