from sqlalchemy import Column, String, Boolean, DateTime, Float, func
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class CuratedVendor(Base):
    __tablename__ = "curated_vendors"
    __table_args__ = {"schema": "curated_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vendorId = Column(String, nullable=False, unique=True) # Make unique for FK
    vendorCode = Column(String, nullable=False)
    vendorName = Column(String, nullable=False)
    gst = Column(String, nullable=True)
    validFrom = Column(DateTime, nullable=False)
    validTo = Column(DateTime, nullable=True)
    isCurrent = Column(Boolean, default=True)
    dqScore = Column(Float, nullable=True)
    createdAt = Column(DateTime, default=func.now())
    nameiy = Column(String, nullable=True)
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    invoices = relationship("CuratedInvoice", back_populates="vendor")
