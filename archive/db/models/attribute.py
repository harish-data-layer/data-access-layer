from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class Attribute(Base):
    __tablename__ = "attributes"
    __table_args__ = {"schema": "semantic_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attributeId = Column(String, unique=True, nullable=False)
    entityId = Column(String, ForeignKey("semantic_layer.entities.entityId"), nullable=False)
    attributeName = Column(String, nullable=False)
    dataType = Column(String, nullable=False)
    businessDefinition = Column(String, nullable=False)
    isSensitive = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    entity = relationship("Entity", back_populates="attributes")
