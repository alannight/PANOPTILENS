"""
Evidence and findings models for investigation management
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class EvidenceStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    EXTRACTED = "EXTRACTED"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    VERIFIED = "VERIFIED"


class EvidenceType(str, enum.Enum):
    IMAGE_METADATA = "IMAGE_METADATA"
    OCR_TEXT = "OCR_TEXT"
    PUBLIC_SOURCE = "PUBLIC_SOURCE"
    MAP_INFORMATION = "MAP_INFORMATION"
    DOCUMENT = "DOCUMENT"
    USER_OBSERVATION = "USER_OBSERVATION"
    TECHNICAL_ANALYSIS = "TECHNICAL_ANALYSIS"


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    type = Column(Enum(EvidenceType), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    
    status = Column(Enum(EvidenceStatus), default=EvidenceStatus.UNVERIFIED, nullable=False)
    
    # Foreign keys
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(String, ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Raw data (JSON)
    raw_data = Column(Text, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="evidence_items")
    image = relationship("Image")

    def __repr__(self):
        return f"<EvidenceItem(id={self.id}, type={self.type}, status={self.status})>"


class ConfidenceLevel(str, enum.Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.MEDIUM, nullable=False)
    status = Column(Enum(EvidenceStatus), default=EvidenceStatus.UNVERIFIED, nullable=False)
    
    # Evidence supporting this finding
    evidence_ids = Column(Text, nullable=True)  # JSON array of evidence IDs
    
    # Limitations and caveats
    limitations = Column(Text, nullable=True)
    
    # Foreign keys
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="findings")

    def __repr__(self):
        return f"<Finding(id={self.id}, title={self.title}, confidence={self.confidence})>"
