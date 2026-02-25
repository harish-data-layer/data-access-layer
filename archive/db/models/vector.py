from sqlalchemy import Column, String, DateTime, func
from db.base import Base
import uuid

class VendorEmbedding(Base):
    __tablename__ = "vendor_embeddings"
    __table_args__ = {"schema": "vector_layer"}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vendorId = Column(String, unique=True, nullable=False)
    embedding = Column(String, nullable=False) # Prisma Schema says String, implies serialized vector or unsupported type
    model = Column(String, default="text-embedding-ada-002")
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
