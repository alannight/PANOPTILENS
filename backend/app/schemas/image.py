from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union, List
from datetime import datetime


class ImageUpload(BaseModel):
    filename: str
    content_type: str


class CameraMetadata(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    lens: Optional[str] = None
    software: Optional[str] = None


class CaptureMetadata(BaseModel):
    dateTimeOriginal: Optional[str] = None
    createDate: Optional[str] = None
    modifyDate: Optional[str] = None
    dateTimeDigitized: Optional[str] = None
    offsetTimeOriginal: Optional[str] = None
    offsetTimeDigitized: Optional[str] = None
    offsetTime: Optional[str] = None
    timezoneUnknown: bool = True
    timezoneUnknowns: Dict[str, bool] = Field(default_factory=dict)
    serverReceivedAt: Optional[str] = None
    fileUploadTimestamp: Optional[str] = None


class AddressData(BaseModel):
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    road: Optional[str] = None
    formatted: Optional[str] = None


class GeographicMetadata(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    gpsTimestamp: Optional[str] = None
    direction: Optional[float] = None
    address: Optional[AddressData] = None


class ImageDetails(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    orientation: Optional[Union[str, int]] = None
    colorSpace: Optional[str] = None
    resolution: Optional[Any] = None
    format: Optional[str] = None
    mode: Optional[str] = None


class ImageMetadata(BaseModel):
    camera: CameraMetadata
    capture: CaptureMetadata
    geographic: Optional[GeographicMetadata] = None
    image: ImageDetails
    status: str = "NOT_PRESENT"
    gpsStatus: str = "NOT_PRESENT"
    raw: Dict[str, Any] = Field(default_factory=dict)
    derived: Dict[str, Any] = Field(default_factory=dict)
    fieldSources: Dict[str, Optional[str]] = Field(default_factory=dict)


class HashData(BaseModel):
    md5: str
    sha1: str
    sha256: str
    sha512: str


class ForensicStatus(BaseModel):
    mime_validated: Optional[bool] = None
    magic_bytes_validated: Optional[bool] = None
    extension_match: Optional[bool] = None
    image_decoded: Optional[bool] = None
    metadata_extracted: Optional[bool] = None
    metadata_consistency: str = "NOT_ASSESSED"


class ImageResponse(BaseModel):
    id: str
    caseId: Optional[str] = None
    userId: Optional[str] = None
    filename: str
    size: int
    type: str
    format: Optional[str] = None
    mode: Optional[str] = None
    url: str
    hash: HashData
    metadata: ImageMetadata
    forensic: ForensicStatus = Field(default_factory=ForensicStatus)
    uploadedAt: datetime
    processedAt: Optional[datetime] = None
    metadataExtractedAt: Optional[datetime] = None
    isDeleted: bool = False
    deletedAt: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    analystNotes: Optional[str] = None
    
    class Config:
        from_attributes = True


class ImageAnnotationsUpdate(BaseModel):
    tags: Optional[List[str]] = None
    analystNotes: Optional[str] = None


class DeletionAuditResponse(BaseModel):
    id: str
    imageId: str
    filename: str
    sha256: Optional[str] = None
    action: str
    occurredAt: datetime
