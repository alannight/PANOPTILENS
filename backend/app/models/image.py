"""
Image model for uploaded forensic evidence
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    image_format = Column(String, nullable=True)
    image_mode = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)  # Path or key in storage system
    
    # Foreign keys
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    case_id = Column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)

    # Lifecycle and analyst annotations
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(Text, default="[]", nullable=False)
    analyst_notes = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="images")
    case = relationship("Case", back_populates="images")
    hashes = relationship("ImageHash", back_populates="image", cascade="all, delete-orphan", uselist=False)
    image_metadata = relationship("ImageMetadata", back_populates="image", cascade="all, delete-orphan", uselist=False)
    forensic_analysis = relationship("ForensicAnalysis", back_populates="image", cascade="all, delete-orphan", uselist=False)
    ocr_results = relationship("OCRResult", back_populates="image", cascade="all, delete-orphan")
    clues = relationship("Clue", back_populates="image", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Image(id={self.id}, filename={self.filename})>"


class ImageHash(Base):
    __tablename__ = "image_hashes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    md5 = Column(String(32), nullable=False)
    sha1 = Column(String(40), nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)  # Primary forensic identifier
    sha512 = Column(String(128), nullable=False)
    
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    image = relationship("Image", back_populates="hashes")

    def __repr__(self):
        return f"<ImageHash(image_id={self.image_id}, sha256={self.sha256[:16]}...)>"


class ImageDeletionAudit(Base):
    __tablename__ = "image_deletion_audits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=True)
    sha256 = Column(String(64), nullable=True)
    action = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ImageDeletionAudit(image_id={self.image_id}, action={self.action})>"


class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Camera metadata
    camera_make = Column(String, nullable=True)
    camera_model = Column(String, nullable=True)
    lens_model = Column(String, nullable=True)
    software = Column(String, nullable=True)
    
    # Capture metadata
    datetime_original = Column(DateTime(timezone=True), nullable=True)
    datetime_digitized = Column(DateTime(timezone=True), nullable=True)
    create_date = Column(DateTime(timezone=True), nullable=True)
    modify_date = Column(DateTime(timezone=True), nullable=True)
    
    # Geographic metadata
    gps_latitude = Column(String, nullable=True)  # Store as string for precision
    gps_longitude = Column(String, nullable=True)
    gps_altitude = Column(String, nullable=True)
    gps_timestamp = Column(String, nullable=True)
    gps_direction = Column(String, nullable=True)
    metadata_status = Column(String, nullable=False, default="NOT_PRESENT")
    gps_status = Column(String, nullable=False, default="NOT_PRESENT")
    
    # Reverse Geocoding
    address_country = Column(String, nullable=True)
    address_province = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_district = Column(String, nullable=True)
    address_road = Column(String, nullable=True)
    address_formatted = Column(String, nullable=True)

    # Timezone Offsets
    offset_time_original = Column(String, nullable=True)
    offset_time_digitized = Column(String, nullable=True)
    offset_time = Column(String, nullable=True)

    # File System Timestamps
    file_upload_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Image properties
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    orientation = Column(String, nullable=True)
    color_space = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    
    # Raw EXIF data (JSON)
    raw_exif = Column(Text, nullable=True)
    derived_metadata = Column(Text, nullable=True)
    field_sources = Column(Text, nullable=True)
    
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    image = relationship("Image", back_populates="image_metadata")

    def __repr__(self):
        return f"<ImageMetadata(image_id={self.image_id})>"


class ForensicAnalysis(Base):
    __tablename__ = "forensic_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # File validation
    mime_validated = Column(Boolean, default=False)
    magic_bytes_validated = Column(Boolean, default=False)
    extension_match = Column(Boolean, default=False)
    image_decoded = Column(Boolean, default=False)
    
    # Structural analysis
    has_exif = Column(Boolean, default=False)
    has_gps = Column(Boolean, default=False)
    has_thumbnail = Column(Boolean, default=False)
    
    # Integrity
    metadata_consistent = Column(Boolean, nullable=True, default=None)
    timestamp_anomalies = Column(Text, nullable=True)
    
    # Detected anomalies
    anomalies = Column(Text, nullable=True)  # JSON array
    
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    image = relationship("Image", back_populates="forensic_analysis")

    def __repr__(self):
        return f"<ForensicAnalysis(image_id={self.image_id})>"
