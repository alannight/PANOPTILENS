from pydantic import BaseModel
from typing import Optional, Dict, Any
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


class GeographicMetadata(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    gpsTimestamp: Optional[str] = None


class ImageDetails(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    orientation: Optional[str] = None
    colorSpace: Optional[str] = None
    resolution: Optional[str] = None


class ImageMetadata(BaseModel):
    camera: CameraMetadata
    capture: CaptureMetadata
    geographic: Optional[GeographicMetadata] = None
    image: ImageDetails


class HashData(BaseModel):
    md5: str
    sha1: str
    sha256: str
    sha512: str


class ImageResponse(BaseModel):
    id: str
    filename: str
    size: int
    type: str
    url: str
    hash: HashData
    metadata: ImageMetadata
    uploadedAt: datetime
    
    class Config:
        from_attributes = True
