from sqlalchemy import Column, String, Integer, Text, func, DateTime
from db.base import Base

class SemanticLayer(Base):
    """Layer-1(Semantic) converted from Excel"""
    __tablename__ = "layer_1_semantic"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    SEMANTIC_ENTITY = Column(Text)
    SEMANTIC_ATTRIBUTE = Column(Text)
    BUSINESS_DESCRIPTION = Column(Text)
    BUSINESS_RULE = Column(Text)
    LOGICAL_DATA_TYPE = Column(Text)
    MANDATORY_YN = Column(Text)
    ALLOWED_VALUESPATTERN = Column(Text)
    SENSITIVITY_CLASSIFICATION = Column(Text)
    AI_USAGE_CONTEXT = Column(Text)
    DATA_OWNER = Column(Text)
    QUALITY_EXPECTATION = Column(Text)
    REMARKS = Column(Text)
    created_at = Column(DateTime, default=func.now())

class AiCuratedLayer(Base):
    """Layer-2(AI-Curated) converted from Excel"""
    __tablename__ = "layer_2_ai_curated"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    SEMANTIC_ATTRIBUTE = Column(Text)
    CURATED_COLUMN = Column(Text)
    DATA_TYPE = Column(Text)
    TRANSFORMATION = Column(Text)
    QUALITY_RULE = Column(Text)
    AI_READY = Column(Text)
    USAGE = Column(Text)
    created_at = Column(DateTime, default=func.now())

class IntegrationPull(Base):
    """Layer-3A(Integration-Pull) converted from Excel"""
    __tablename__ = "layer_3a_integration_pull"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    CURATED_COLUMN = Column(Text)
    SOURCE_SYSTEM = Column(Text)
    SAP_OBJECT = Column(Text)
    FIELD = Column(Text)
    EXTRACTION = Column(Text)
    INCREMENTAL = Column(Text)
    PURPOSE = Column(Text)
    created_at = Column(DateTime, default=func.now())

class IntegrationPush(Base):
    """Layer-3B(Integration-Push) converted from Excel"""
    __tablename__ = "layer_3b_integration_push"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    CURATED_COLUMN = Column(Text)
    TARGET_SYSTEM = Column(Text)
    SAP_MODULE = Column(Text)
    INTERFACE = Column(Text)
    FIELD = Column(Text)
    SAP_OBJECT = Column(Text)
    TRIGGER = Column(Text)
    PURPOSE = Column(Text)
    created_at = Column(DateTime, default=func.now())

class PublicCloudLayer(Base):
    """Layer-3(PublicCloud) converted from Excel"""
    __tablename__ = "layer_3_publiccloud"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now())

