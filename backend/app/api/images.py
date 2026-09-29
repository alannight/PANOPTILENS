from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import logging

from app.database import get_db
from app.models.image import Image, ImageHash, ImageMetadata, ForensicAnalysis
from app.services.metadata_extractor import MetadataExtractor
from app.services.hash_calculator import HashCalculator
from app.services.storage import storage_service, UploadTooLargeError
from app.services.image_validation import ImageValidationError, validate_and_inspect
from app.schemas.image import ImageResponse, HashData, ImageMetadata as ImageMetadataSchema, ForensicStatus

logger = logging.getLogger(__name__)

def require_image_access_context() -> None:
    if os.getenv("APP_ENV", "production").lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_NOT_CONFIGURED", "message": "Image access is disabled until authentication is configured."},
        )


router = APIRouter(dependencies=[Depends(require_image_access_context)])

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _error(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": code, "message": message})


def _parse_exif_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def _image_response(image: Image) -> ImageResponse:
    hashes = image.hashes
    metadata = image.image_metadata
    raw = {}
    if metadata and metadata.raw_exif:
        try:
            raw = json.loads(metadata.raw_exif)
        except (TypeError, json.JSONDecodeError):
            raw = {}
    resolution = metadata.resolution if metadata else None
    if isinstance(resolution, str):
        try:
            resolution = json.loads(resolution)
        except json.JSONDecodeError:
            pass

    geographic = None
    if metadata and metadata.gps_latitude is not None and metadata.gps_longitude is not None:
        geographic = {
            "latitude": float(metadata.gps_latitude),
            "longitude": float(metadata.gps_longitude),
            "altitude": float(metadata.gps_altitude) if metadata.gps_altitude is not None else None,
            "gpsTimestamp": metadata.gps_timestamp,
            "direction": float(metadata.gps_direction) if metadata.gps_direction is not None else None,
        }

    forensic = image.forensic_analysis
    return ImageResponse(
        id=image.id,
        filename=image.original_filename,
        size=image.size,
        type=image.mime_type,
        format=image.image_format,
        mode=image.image_mode,
        url=f"/api/images/{image.id}/file",
        hash=HashData(md5=hashes.md5, sha1=hashes.sha1, sha256=hashes.sha256, sha512=hashes.sha512),
        metadata=ImageMetadataSchema(
            camera={
                "make": metadata.camera_make,
                "model": metadata.camera_model,
                "lens": metadata.lens_model,
                "software": metadata.software,
            },
            capture={
                "dateTimeOriginal": raw.get("DateTimeOriginal"),
                "createDate": raw.get("DateTime"),
                "modifyDate": raw.get("DateTime"),
                "dateTimeDigitized": raw.get("DateTimeDigitized"),
            },
            geographic=geographic,
            image={
                "width": metadata.width,
                "height": metadata.height,
                "orientation": metadata.orientation,
                "colorSpace": metadata.color_space,
                "resolution": resolution,
                "format": image.image_format,
                "mode": image.image_mode,
            },
            status=metadata.metadata_status,
            gpsStatus=metadata.gps_status,
            raw=raw,
        ),
        forensic=ForensicStatus(
            mime_validated=forensic.mime_validated if forensic else None,
            magic_bytes_validated=forensic.magic_bytes_validated if forensic else None,
            extension_match=forensic.extension_match if forensic else None,
            image_decoded=forensic.image_decoded if forensic else None,
            metadata_extracted=(metadata.metadata_status != "FAILED") if metadata else None,
            metadata_consistency="NOT_ASSESSED" if not forensic or forensic.metadata_consistent is None else "ASSESSED",
        ),
        uploadedAt=image.uploaded_at,
        caseId=image.case_id,
        userId=image.owner_id,
    )


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    case_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Validate, hash, extract metadata, and persist an original image."""
    staged_path = None
    storage_key = None
    committed = False
    try:
        raw_filename = Path((file.filename or "upload").replace("\\", "/")).name
        original_filename = re.sub(r"[\x00-\x1f\x7f]", "", raw_filename)[:255] or "upload"
        file.file.seek(0)
        staged_path, file_size = storage_service.stage_upload(file.file, MAX_UPLOAD_SIZE)
        inspection = validate_and_inspect(staged_path, original_filename)

        logger.info("image_upload stage=validation status=completed format=%s size=%s", inspection["format"], file_size)
        hashes = HashCalculator.calculate_hashes(str(staged_path))
        logger.info("image_upload stage=hash status=completed sha256=%s", hashes["sha256"])
        metadata_dict = MetadataExtractor.extract_exif(staged_path)
        logger.info(
            "image_upload stage=metadata_extraction status=%s fields_extracted=%s gps_present=%s",
            metadata_dict["status"], len(metadata_dict["raw"]), metadata_dict["gpsStatus"] == "PRESENT",
        )

        storage_key = storage_service.generate_storage_key(original_filename, inspection["format"])
        storage_service.promote(staged_path, storage_key)
        staged_path = None
        image = Image(
            filename=storage_key,
            original_filename=original_filename,
            size=file_size,
            mime_type=inspection["mime_type"],
            image_format=inspection["format"],
            image_mode=inspection["mode"],
            storage_path=storage_key,
            owner_id=None,
            case_id=case_id,
            uploaded_at=_utcnow(),
            is_processed=True,
            processed_at=_utcnow()
        )
        db.add(image)
        db.flush()

        # Create hash record
        image_hash = ImageHash(
            image_id=image.id,
            md5=hashes["md5"],
            sha1=hashes["sha1"],
            sha256=hashes["sha256"],
            sha512=hashes["sha512"],
            calculated_at=_utcnow()
        )
        db.add(image_hash)

        raw_exif = metadata_dict["raw"]
        geographic = metadata_dict.get("geographic")
        image_metadata = ImageMetadata(
            image_id=image.id,
            camera_make=metadata_dict["camera"].get("make"),
            camera_model=metadata_dict["camera"].get("model"),
            lens_model=metadata_dict["camera"].get("lens"),
            software=metadata_dict["camera"].get("software"),
            datetime_original=_parse_exif_datetime(metadata_dict["capture"].get("dateTimeOriginal")),
            datetime_digitized=_parse_exif_datetime(metadata_dict["capture"].get("dateTimeDigitized")),
            create_date=_parse_exif_datetime(metadata_dict["capture"].get("createDate")),
            modify_date=_parse_exif_datetime(metadata_dict["capture"].get("modifyDate")),
            width=inspection["width"],
            height=inspection["height"],
            orientation=str(metadata_dict["image"].get("orientation")) if metadata_dict["image"].get("orientation") is not None else None,
            color_space=str(metadata_dict["image"].get("colorSpace")) if metadata_dict["image"].get("colorSpace") is not None else None,
            resolution=json.dumps(metadata_dict["image"].get("resolution")),
            raw_exif=json.dumps(raw_exif, ensure_ascii=False),
            metadata_status=metadata_dict["status"],
            gps_status=metadata_dict["gpsStatus"],
            extracted_at=_utcnow(),
        )
        if geographic:
            image_metadata.gps_latitude = str(geographic["latitude"])
            image_metadata.gps_longitude = str(geographic["longitude"])
            image_metadata.gps_altitude = str(geographic["altitude"]) if geographic["altitude"] is not None else None
            image_metadata.gps_timestamp = geographic["gpsTimestamp"]
            image_metadata.gps_direction = str(geographic["direction"]) if geographic["direction"] is not None else None
        db.add(image_metadata)

        forensic = ForensicAnalysis(
            image_id=image.id,
            mime_validated=True,
            magic_bytes_validated=True,
            extension_match=inspection["extension_match"],
            image_decoded=True,
            has_exif=metadata_dict["status"] == "PRESENT",
            has_gps=metadata_dict["gpsStatus"] == "PRESENT",
            metadata_consistent=None,
            analyzed_at=_utcnow()
        )
        db.add(forensic)
        db.commit()
        committed = True
        db.refresh(image)

        logger.info("image_upload image_id=%s stage=persistence status=completed", image.id)
        return _image_response(image)
    except UploadTooLargeError:
        return _error("FILE_TOO_LARGE", "Uploaded file exceeds the configured maximum size.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    except ImageValidationError as exc:
        code_to_status = {"UNSUPPORTED_FORMAT": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                          "IMAGE_DIMENSIONS_UNSAFE": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE}
        return _error(exc.code, exc.message, code_to_status.get(exc.code, status.HTTP_400_BAD_REQUEST))
    except ValueError as exc:
        if str(exc) == "Empty upload":
            return _error("INVALID_FILE", "The uploaded file is empty.", status.HTTP_400_BAD_REQUEST)
        db.rollback()
        logger.exception("image_upload stage=failed")
        return _error("INTERNAL_ERROR", "Image processing failed.", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("image_upload stage=failed error_type=%s", type(e).__name__)
        return _error("INTERNAL_ERROR", "Image processing failed.", status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if staged_path is not None:
            staged_path.unlink(missing_ok=True)
        if storage_key and not committed and storage_service.exists(storage_key):
            storage_service.delete(storage_key)


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str, db: Session = Depends(get_db)):
    """Get image details by ID"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        return _error("IMAGE_NOT_FOUND", "Image was not found.", status.HTTP_404_NOT_FOUND)
    if not image.hashes or not image.image_metadata:
        return _error("INTERNAL_ERROR", "Image analysis data is unavailable.", status.HTTP_500_INTERNAL_SERVER_ERROR)
    return _image_response(image)


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
    
    return [_image_response(image) for image in images if image.hashes and image.image_metadata]


@router.get("/{image_id}/file")
async def get_image_file(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        return _error("IMAGE_NOT_FOUND", "Image was not found.", status.HTTP_404_NOT_FOUND)
    image_path = storage_service.get(image.storage_path)
    if image_path is None:
        return _error("IMAGE_NOT_FOUND", "Stored image file was not found.", status.HTTP_404_NOT_FOUND)
    return FileResponse(image_path, media_type=image.mime_type, headers={"Content-Disposition": "inline"})


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
    
    storage_path = image.storage_path
    db.delete(image)
    db.commit()

    try:
        storage_service.delete(storage_path)
    except Exception as e:
        logger.error("image_delete storage_cleanup=failed error_type=%s", type(e).__name__)
    
    return {"message": "Image deleted successfully"}
