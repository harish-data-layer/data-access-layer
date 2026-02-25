from sqlalchemy import Column, String, DateTime, func, ARRAY
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = {"schema": "semantic_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entityId = Column(String, unique=True, nullable=False)
    entityName = Column(String, nullable=False)
    businessDefinition = Column(String, nullable=False)
    businessOwner = Column(String, nullable=False)
    dataSteward = Column(String, nullable=False)
    sourceSystem = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    dataClassification = Column(String, nullable=False)
    complianceTags = Column(ARRAY(String))
    retentionPolicy = Column(String, nullable=False)
    versionId = Column(String, nullable=False)
    effectiveFrom = Column(DateTime, nullable=False)
    effectiveTo = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    attributes = relationship("Attribute", back_populates="entity")
