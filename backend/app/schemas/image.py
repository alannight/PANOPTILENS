from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union
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


class GeographicMetadata(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    gpsTimestamp: Optional[str] = None
    direction: Optional[float] = None


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
    
    class Config:
        from_attributes = True
