"""
Analysis models for OCR, clues, and OSINT
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    language = Column(String, nullable=True)
    
    # Bounding box data (JSON)
    bounding_boxes = Column(Text, nullable=True)
    
    # OCR engine used
    engine = Column(String, nullable=True)
    
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    image = relationship("Image", back_populates="ocr_results")

    def __repr__(self):
        return f"<OCRResult(image_id={self.image_id}, text={self.text[:50]}...)>"


class ClueType(str, enum.Enum):
    LOCATION = "LOCATION"
    DATE = "DATE"
    TIME = "TIME"
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    URL = "URL"
    DOMAIN = "DOMAIN"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    COORDINATE = "COORDINATE"
    VEHICLE_ID = "VEHICLE_ID"
    BUILDING = "BUILDING"
    LANDMARK = "LANDMARK"
    SIGN = "SIGN"
    OBJECT = "OBJECT"
    ORGANIZATION = "ORGANIZATION"
    PERSON = "PERSON"
    OTHER = "OTHER"


class ClueSource(str, enum.Enum):
    EXIF = "EXIF"
    OCR = "OCR"
    VISUAL_ANALYSIS = "VISUAL_ANALYSIS"
    FILENAME = "FILENAME"
    USER_ADDED = "USER_ADDED"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"


class ClueStatus(str, enum.Enum):
    EXTRACTED = "EXTRACTED"
    UNVERIFIED = "UNVERIFIED"
    INVESTIGATING = "INVESTIGATING"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    VERIFIED = "VERIFIED"


class Clue(Base):
    __tablename__ = "clues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    type = Column(Enum(ClueType), nullable=False)
    value = Column(String, nullable=False)
    
    source = Column(Enum(ClueSource), nullable=False)
    confidence = Column(String, nullable=True)  # LOW, MEDIUM, HIGH, VERY_HIGH
    
    status = Column(Enum(ClueStatus), default=ClueStatus.EXTRACTED, nullable=False)
    
    # Foreign keys
    image_id = Column(String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    
    # Related evidence or sources
    related_evidence_ids = Column(Text, nullable=True)  # JSON array
    
    # User notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    image = relationship("Image", back_populates="clues")

    def __repr__(self):
        return f"<Clue(id={self.id}, type={self.type}, value={self.value})>"


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Event timestamp (the time the event occurred, not when it was recorded)
    event_timestamp = Column(DateTime, nullable=False)
    
    # Source of the timestamp
    timestamp_source = Column(String, nullable=False)  # EXIF, OCR, User Added, etc.
    
    # Foreign keys
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(String, ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    
    # When this event was recorded in the system
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="timeline_events")
    image = relationship("Image")

    def __repr__(self):
        return f"<TimelineEvent(id={self.id}, title={self.title}, timestamp={self.event_timestamp})>"
