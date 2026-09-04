from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime
import logging

from app.database import get_db
from app.models.image import Image, ImageHash, ImageMetadata, ForensicAnalysis
from app.services.metadata_extractor import MetadataExtractor
from app.services.hash_calculator import HashCalculator
from app.services.storage import storage_service
from app.schemas.image import ImageResponse, HashData, ImageMetadata as ImageMetadataSchema

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB default
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}"
        )


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    case_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload and analyze an image"""
    temp_file_path = None
    storage_key = None
    
    try:
        # Validate file
        validate_image(file)
        
        # Generate storage key
        storage_key = storage_service.generate_storage_key(file.filename)
        
        # Save to storage
        file.file.seek(0)  # Reset file pointer
        storage_service.save(file.file, storage_key)
        
        # Get file path for processing
        temp_file_path = storage_service.get(storage_key)
        
        if not temp_file_path or not temp_file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file to storage"
            )
        
        # Check file size
        file_size = storage_service.get_size(storage_key)
        if file_size > MAX_UPLOAD_SIZE:
            storage_service.delete(storage_key)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum of {MAX_UPLOAD_SIZE} bytes"
            )
        
        # Calculate hashes
        logger.info(f"Calculating hashes for {storage_key}")
        hashes = HashCalculator.calculate_hashes(str(temp_file_path))
        
        # Extract metadata
        logger.info(f"Extracting metadata for {storage_key}")
        metadata_dict = MetadataExtractor.extract_exif(str(temp_file_path))
        
        # Create database record
        image = Image(
            filename=storage_key,
            original_filename=file.filename,
            size=file_size,
            mime_type=file.content_type,
            storage_path=storage_key,
            owner_id="system",  # TODO: Replace with actual user ID when auth is implemented
            case_id=case_id,
            uploaded_at=datetime.utcnow(),
            is_processed=True,
            processed_at=datetime.utcnow()
        )
        
        db.add(image)
        db.flush()  # Get image ID
        
        # Create hash record
        image_hash = ImageHash(
            image_id=image.id,
            md5=hashes["md5"],
            sha1=hashes["sha1"],
            sha256=hashes["sha256"],
            sha512=hashes["sha512"],
            calculated_at=datetime.utcnow()
        )
        db.add(image_hash)
        
        # Create metadata record
        image_metadata = ImageMetadata(
            image_id=image.id,
            camera_make=metadata_dict["camera"].get("make"),
            camera_model=metadata_dict["camera"].get("model"),
            lens_model=metadata_dict["camera"].get("lens"),
            software=metadata_dict["camera"].get("software"),
            width=metadata_dict["image"].get("width"),
            height=metadata_dict["image"].get("height"),
            orientation=metadata_dict["image"].get("orientation"),
            color_space=metadata_dict["image"].get("colorSpace"),
            resolution=metadata_dict["image"].get("resolution"),
            extracted_at=datetime.utcnow()
        )
        
        # Handle GPS data if available
        if metadata_dict.get("geographic"):
            geo = metadata_dict["geographic"]
            image_metadata.gps_latitude = str(geo["latitude"]) if geo.get("latitude") else None
            image_metadata.gps_longitude = str(geo["longitude"]) if geo.get("longitude") else None
            image_metadata.gps_altitude = str(geo["altitude"]) if geo.get("altitude") else None
            image_metadata.gps_timestamp = geo.get("gpsTimestamp")
        
        db.add(image_metadata)
        
        # Create forensic analysis record
        forensic = ForensicAnalysis(
            image_id=image.id,
            mime_validated=True,
            extension_match=True,
            has_exif=bool(metadata_dict["camera"].get("make") or metadata_dict["camera"].get("model")),
            has_gps=bool(metadata_dict.get("geographic")),
            metadata_consistent=True,
            analyzed_at=datetime.utcnow()
        )
        db.add(forensic)
        
        # Commit transaction
        db.commit()
        db.refresh(image)
        
        logger.info(f"Image uploaded successfully: {image.id}")
        
        # Build response
        response = ImageResponse(
            id=image.id,
            filename=file.filename,
            size=file_size,
            type=file.content_type,
            url=storage_service.get_url(storage_key),
            hash=HashData(**hashes),
            metadata=ImageMetadataSchema(**metadata_dict),
            uploadedAt=image.uploaded_at.isoformat(),
            caseId=case_id
        )
        
        return response
        
    except HTTPException:
        # Clean up storage if HTTP exception
        if storage_key and storage_service.exists(storage_key):
            storage_service.delete(storage_key)
        db.rollback()
        raise
    except Exception as e:
        # Clean up on any error
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        if storage_key and storage_service.exists(storage_key):
            storage_service.delete(storage_key)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str, db: Session = Depends(get_db)):
    """Get image details by ID"""
    # Query image with relationships
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Get hash data
    hashes = image.hashes
    if not hashes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image hash data not found"
        )
    
    # Get metadata
    metadata = image.image_metadata
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image metadata not found"
        )
    
    # Build metadata response
    metadata_dict = {
        "camera": {
            "make": metadata.camera_make,
            "model": metadata.camera_model,
            "lens": metadata.lens_model,
            "software": metadata.software,
        },
        "capture": {
            "dateTimeOriginal": metadata.datetime_original.isoformat() if metadata.datetime_original else None,
            "createDate": metadata.create_date.isoformat() if metadata.create_date else None,
            "modifyDate": metadata.modify_date.isoformat() if metadata.modify_date else None,
        },
        "geographic": None,
        "image": {
            "width": metadata.width,
            "height": metadata.height,
            "orientation": metadata.orientation,
            "colorSpace": metadata.color_space,
            "resolution": metadata.resolution,
        },
    }
    
    # Add GPS data if available
    if metadata.gps_latitude and metadata.gps_longitude:
        metadata_dict["geographic"] = {
            "latitude": float(metadata.gps_latitude),
            "longitude": float(metadata.gps_longitude),
            "altitude": float(metadata.gps_altitude) if metadata.gps_altitude else None,
            "gpsTimestamp": metadata.gps_timestamp,
        }
    
    # Build response
    response = ImageResponse(
        id=image.id,
        filename=image.original_filename,
        size=image.size,
        type=image.mime_type,
        url=storage_service.get_url(image.storage_path),
        hash=HashData(
            md5=hashes.md5,
            sha1=hashes.sha1,
            sha256=hashes.sha256,
            sha512=hashes.sha512
        ),
        metadata=ImageMetadataSchema(**metadata_dict),
        uploadedAt=image.uploaded_at.isoformat(),
        caseId=image.case_id,
        userId=image.owner_id
    )
    
    return response


@router.get("/", response_model=List[ImageResponse])
async def get_images(
    case_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all images (optionally filtered by case)"""
    query = db.query(Image)
    
    if case_id:
        query = query.filter(Image.case_id == case_id)
    
    images = query.order_by(Image.uploaded_at.desc()).all()
    
    # Build response list
    response = []
    for image in images:
        if not image.hashes or not image.image_metadata:
            continue
            
        hashes = image.hashes
        metadata = image.image_metadata
        
        metadata_dict = {
            "camera": {
                "make": metadata.camera_make,
                "model": metadata.camera_model,
                "lens": metadata.lens_model,
                "software": metadata.software,
            },
            "capture": {
                "dateTimeOriginal": metadata.datetime_original.isoformat() if metadata.datetime_original else None,
                "createDate": metadata.create_date.isoformat() if metadata.create_date else None,
                "modifyDate": metadata.modify_date.isoformat() if metadata.modify_date else None,
            },
            "geographic": None,
            "image": {
                "width": metadata.width,
                "height": metadata.height,
                "orientation": metadata.orientation,
                "colorSpace": metadata.color_space,
                "resolution": metadata.resolution,
            },
        }
        
        if metadata.gps_latitude and metadata.gps_longitude:
            metadata_dict["geographic"] = {
                "latitude": float(metadata.gps_latitude),
                "longitude": float(metadata.gps_longitude),
                "altitude": float(metadata.gps_altitude) if metadata.gps_altitude else None,
                "gpsTimestamp": metadata.gps_timestamp,
            }
        
        response.append(ImageResponse(
            id=image.id,
            filename=image.original_filename,
            size=image.size,
            type=image.mime_type,
            url=storage_service.get_url(image.storage_path),
            hash=HashData(
                md5=hashes.md5,
                sha1=hashes.sha1,
                sha256=hashes.sha256,
                sha512=hashes.sha512
            ),
            metadata=ImageMetadataSchema(**metadata_dict),
            uploadedAt=image.uploaded_at.isoformat(),
            caseId=image.case_id,
            userId=image.owner_id
        ))
    
    return response


@router.delete("/{image_id}")
async def delete_image(image_id: str, db: Session = Depends(get_db)):
    """Delete an image"""
    # Query image
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete from storage
    try:
        storage_service.delete(image.storage_path)
    except Exception as e:
        logger.error(f"Failed to delete image from storage: {str(e)}")
        # Continue with database deletion even if storage deletion fails
    
    # Delete from database (cascades to related records)
    db.delete(image)
    db.commit()
    
    return {"message": "Image deleted successfully"}
