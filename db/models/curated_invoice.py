from sqlalchemy import Column, String, Boolean, DateTime, Float, func, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base
import uuid

class CuratedInvoice(Base):
    __tablename__ = "curated_invoices"
    __table_args__ = {"schema": "curated_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoiceId = Column(String, nullable=False)
    invoiceNumber = Column(String, nullable=False)
    vendorId = Column(String, ForeignKey("curated_layer.curated_vendors.vendorId"), nullable=False) # FK to vendorId
    
    invoiceDate = Column(DateTime, nullable=False)
    totalAmount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, nullable=False)
    validFrom = Column(DateTime, nullable=False)
    validTo = Column(DateTime, nullable=True)
    isCurrent = Column(Boolean, default=True)
    dqScore = Column(Float, nullable=True)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())

    vendor = relationship("CuratedVendor", back_populates="invoices")
