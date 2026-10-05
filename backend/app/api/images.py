from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
import re
import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path
import logging

from app.database import get_db
from app.models.image import Image, ImageHash, ImageMetadata, ForensicAnalysis, ImageDeletionAudit
from app.models.case import Case
from app.services.metadata_extractor import MetadataExtractor, parse_exif_datetime
from app.services.hash_calculator import HashCalculator
from app.services.storage import storage_service, UploadTooLargeError
from app.services.image_validation import ImageValidationError, validate_and_inspect
from app.services.geocoding import GeocodingProvider, default_geocoder
from app.schemas.image import (
    ImageResponse,
    HashData,
    ImageMetadata as ImageMetadataSchema,
    ForensicStatus,
    ImageAnnotationsUpdate,
    DeletionAuditResponse,
)

logger = logging.getLogger(__name__)

def require_image_access_context() -> None:
    if os.getenv("APP_ENV", "production").lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AUTH_NOT_CONFIGURED", "message": "Image access is disabled until authentication is configured."},
        )


router = APIRouter(dependencies=[Depends(require_image_access_context)])

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 104857600))


def get_geocoding_provider() -> GeocodingProvider:
    return default_geocoder


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _error(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": code, "message": message})


def _hard_delete_image(db: Session, image: Image) -> None:
    quarantine_path = storage_service.quarantine(image.storage_path)
    audit = ImageDeletionAudit(
        image_id=image.id,
        filename=image.original_filename,
        storage_key=image.storage_path,
        sha256=image.hashes.sha256 if image.hashes else None,
        action="HARD_DELETE",
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.delete(image)
    try:
        db.commit()
    except Exception:
        db.rollback()
        if quarantine_path is not None:
            storage_service.restore_quarantined(quarantine_path, image.storage_path)
        raise
    if quarantine_path is not None:
        storage_service.purge_quarantined(quarantine_path)


def _parse_exif_datetime(value: Optional[str], offset: Optional[str] = None) -> Optional[datetime]:
    return parse_exif_datetime(value, offset)


def _image_response(image: Image) -> ImageResponse:
    hashes = image.hashes
    metadata = image.image_metadata
    raw = {}
    derived = {}
    if metadata and metadata.raw_exif:
        try:
            raw = json.loads(metadata.raw_exif)
        except (TypeError, json.JSONDecodeError):
            raw = {}
    if metadata and metadata.derived_metadata:
        try:
            derived = json.loads(metadata.derived_metadata)
        except (TypeError, json.JSONDecodeError):
            derived = {}
    try:
        tags = json.loads(image.tags or "[]")
        if not isinstance(tags, list):
            tags = []
    except (TypeError, json.JSONDecodeError):
        tags = []
    resolution = metadata.resolution if metadata else None
    if isinstance(resolution, str):
        try:
            resolution = json.loads(resolution)
        except json.JSONDecodeError:
            pass

    geographic = None
    if metadata and metadata.gps_latitude is not None and metadata.gps_longitude is not None:
        address_data = None
        if any((
            metadata.address_country,
            metadata.address_province,
            metadata.address_city,
            metadata.address_district,
            metadata.address_road,
            metadata.address_formatted,
        )):
            address_data = {
                "country": metadata.address_country,
                "province": metadata.address_province,
                "city": metadata.address_city,
                "district": metadata.address_district,
                "road": metadata.address_road,
                "formatted": metadata.address_formatted,
            }
        
        geographic = {
            "latitude": float(metadata.gps_latitude),
            "longitude": float(metadata.gps_longitude),
            "altitude": float(metadata.gps_altitude) if metadata.gps_altitude is not None else None,
            "gpsTimestamp": metadata.gps_timestamp,
            "direction": float(metadata.gps_direction) if metadata.gps_direction is not None else None,
            "address": address_data,
        }

    forensic = image.forensic_analysis
    timestamps = derived.get("timestamps", {})
    captured_at = timestamps.get("capturedAt", {})
    digitized_at = timestamps.get("digitizedAt", {})
    modified_at = timestamps.get("modifiedAt", {})
    server_received_at = image.uploaded_at
    if server_received_at.tzinfo is None:
        server_received_at = server_received_at.replace(tzinfo=timezone.utc)
    deleted_at = image.deleted_at
    if deleted_at is not None and deleted_at.tzinfo is None:
        deleted_at = deleted_at.replace(tzinfo=timezone.utc)
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
                "dateTimeOriginal": captured_at.get("value") or raw.get("DateTimeOriginal"),
                "createDate": digitized_at.get("value") or raw.get("DateTimeDigitized"),
                "modifyDate": modified_at.get("value") or raw.get("DateTime"),
                "dateTimeDigitized": digitized_at.get("value") or raw.get("DateTimeDigitized"),
                "offsetTimeOriginal": metadata.offset_time_original if metadata else None,
                "offsetTimeDigitized": metadata.offset_time_digitized if metadata else None,
                "offsetTime": metadata.offset_time if metadata else None,
                "timezoneUnknown": captured_at.get("timezoneUnknown", True),
                "timezoneUnknowns": {
                    "capturedAt": captured_at.get("timezoneUnknown", True),
                    "digitizedAt": digitized_at.get("timezoneUnknown", True),
                    "modifiedAt": modified_at.get("timezoneUnknown", True),
                },
                "serverReceivedAt": server_received_at.isoformat(),
                "fileUploadTimestamp": server_received_at.isoformat(),
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
            derived=derived,
            fieldSources=json.loads(metadata.field_sources) if metadata.field_sources else {},
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
        processedAt=image.processed_at,
        metadataExtractedAt=metadata.extracted_at,
        isDeleted=image.is_deleted,
        deletedAt=deleted_at,
        tags=tags,
        analystNotes=image.analyst_notes,
        caseId=image.case_id,
        userId=image.owner_id,
    )


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    case_id: Optional[str] = None,
    case_id_form: Optional[str] = Form(None, alias="case_id"),
    db: Session = Depends(get_db),
    geocoder: GeocodingProvider = Depends(get_geocoding_provider),
):
    """Validate, hash, extract metadata, and persist an original image."""
    staged_path = None
    storage_key = None
    committed = False
    received_at = _utcnow()
    try:
        case_id = case_id_form or case_id
        if case_id and not db.query(Case).filter(Case.id == case_id).first():
            return _error("CASE_NOT_FOUND", "Case was not found.", status.HTTP_404_NOT_FOUND)
        raw_filename = Path((file.filename or "upload").replace("\\", "/")).name
        original_filename = re.sub(r"[\x00-\x1f\x7f]", "", raw_filename)[:255] or "upload"
        file.file.seek(0)
        staged_path, file_size = storage_service.stage_upload(file.file, MAX_UPLOAD_SIZE)
        inspection = validate_and_inspect(staged_path, original_filename)

        logger.info("image_upload stage=validation status=completed format=%s size=%s", inspection["format"], file_size)
        hashes = HashCalculator.calculate_hashes(str(staged_path))
        logger.info("image_upload stage=hash status=completed sha256=%s", hashes["sha256"])
        metadata_dict = MetadataExtractor.extract_exif(staged_path, original_filename)
        metadata_dict["derived"]["serverReceivedAt"] = received_at.replace(tzinfo=timezone.utc).isoformat()
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
            uploaded_at=received_at,
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
            datetime_original=_parse_exif_datetime(metadata_dict["capture"].get("dateTimeOriginal"), metadata_dict["capture"].get("offsetTimeOriginal")),
            datetime_digitized=_parse_exif_datetime(metadata_dict["capture"].get("dateTimeDigitized"), metadata_dict["capture"].get("offsetTimeDigitized")),
            create_date=_parse_exif_datetime(metadata_dict["capture"].get("createDate"), metadata_dict["capture"].get("offsetTimeDigitized")),
            modify_date=_parse_exif_datetime(metadata_dict["capture"].get("modifyDate"), metadata_dict["capture"].get("offsetTime")),
            offset_time_original=metadata_dict["capture"].get("offsetTimeOriginal"),
            offset_time_digitized=metadata_dict["capture"].get("offsetTimeDigitized"),
            offset_time=metadata_dict["capture"].get("offsetTime"),
            file_upload_timestamp=received_at.replace(tzinfo=timezone.utc),
            width=inspection["width"],
            height=inspection["height"],
            orientation=str(metadata_dict["image"].get("orientation")) if metadata_dict["image"].get("orientation") is not None else None,
            color_space=str(metadata_dict["image"].get("colorSpace")) if metadata_dict["image"].get("colorSpace") is not None else None,
            resolution=json.dumps(metadata_dict["image"].get("resolution")),
            raw_exif=json.dumps(raw_exif, ensure_ascii=False),
            derived_metadata=json.dumps(metadata_dict["derived"], ensure_ascii=False),
            field_sources=json.dumps(metadata_dict["fieldSources"], ensure_ascii=False),
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
            
            # Reverse Geocoding
            address = geocoder.reverse_geocode(geographic["latitude"], geographic["longitude"])
            if address:
                image_metadata.address_country = address.get("country")
                image_metadata.address_province = address.get("province")
                image_metadata.address_city = address.get("city")
                image_metadata.address_district = address.get("district")
                image_metadata.address_road = address.get("road")
                image_metadata.address_formatted = address.get("formatted")
                
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


@router.post("/upload/bulk")
async def upload_images_bulk(
    files: List[UploadFile] = File(...),
    case_id: Optional[str] = None,
    case_id_form: Optional[str] = Form(None, alias="case_id"),
    db: Session = Depends(get_db),
    geocoder: GeocodingProvider = Depends(get_geocoding_provider),
):
    if not files:
        return _error("NO_FILES", "Select at least one image.", status.HTTP_400_BAD_REQUEST)
    if len(files) > 20:
        return _error("BULK_LIMIT_EXCEEDED", "A bulk request may contain at most 20 images.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    selected_case = case_id_form or case_id
    if selected_case and not db.query(Case).filter(Case.id == selected_case).first():
        return _error("CASE_NOT_FOUND", "Case was not found.", status.HTTP_404_NOT_FOUND)

    results = []
    errors = []
    for file in files:
        result = await upload_image(
            file=file,
            case_id=selected_case,
            case_id_form=None,
            db=db,
            geocoder=geocoder,
        )
        if isinstance(result, ImageResponse):
            results.append(result)
            continue
        if isinstance(result, JSONResponse):
            failure = json.loads(result.body.decode("utf-8"))
            errors.append({
                "filename": file.filename,
                "error": failure.get("error", "UPLOAD_FAILED"),
                "message": failure.get("message", "Image upload failed."),
            })
            continue
        errors.append({"filename": file.filename, "error": "UPLOAD_FAILED", "message": "Image upload failed."})

    return {"results": results, "errors": errors}


@router.get("/trash", response_model=List[ImageResponse])
async def list_trash(db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.is_deleted.is_(True)).order_by(Image.deleted_at.desc()).all()
    return [_image_response(image) for image in images if image.hashes and image.image_metadata]


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str, db: Session = Depends(get_db)):
    """Get image details by ID"""
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(False)).first()
    if not image:
        return _error("IMAGE_NOT_FOUND", "Image was not found.", status.HTTP_404_NOT_FOUND)
    if not image.hashes or not image.image_metadata:
        return _error("INTERNAL_ERROR", "Image analysis data is unavailable.", status.HTTP_500_INTERNAL_SERVER_ERROR)
    return _image_response(image)


@router.patch("/{image_id}/annotations")
async def update_image_annotations(
    image_id: str,
    update: ImageAnnotationsUpdate,
    db: Session = Depends(get_db),
):
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(False)).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    if update.tags is not None:
        tags = list(dict.fromkeys(tag.strip() for tag in update.tags if tag.strip()))
        image.tags = json.dumps(tags, ensure_ascii=False)
    if "analystNotes" in update.model_fields_set:
        image.analyst_notes = update.analystNotes
    db.commit()
    return {"tags": json.loads(image.tags or "[]"), "analystNotes": image.analyst_notes}


@router.post("/{image_id}/verify-integrity")
async def verify_image_integrity(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(False)).first()
    if not image or not image.hashes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    path = storage_service.get(image.storage_path)
    checked_at = datetime.now(timezone.utc).isoformat()
    if path is None:
        return {
            "imageId": image.id,
            "status": "MISSING",
            "expectedSha256": image.hashes.sha256,
            "actualSha256": None,
            "checkedAt": checked_at,
        }
    digest = hashlib.sha256()
    try:
        with path.open("rb") as evidence_file:
            for chunk in iter(lambda: evidence_file.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        logger.warning("integrity verification could not read image_id=%s error_type=%s", image_id, type(exc).__name__)
        return {
            "imageId": image.id,
            "status": "UNREADABLE",
            "expectedSha256": image.hashes.sha256,
            "actualSha256": None,
            "checkedAt": checked_at,
        }
    actual_sha256 = digest.hexdigest()
    return {
        "imageId": image.id,
        "status": "VERIFIED" if hmac.compare_digest(actual_sha256, image.hashes.sha256) else "TAMPERED",
        "expectedSha256": image.hashes.sha256,
        "actualSha256": actual_sha256,
        "checkedAt": checked_at,
    }


@router.get("/{image_id}/export")
async def export_image_profile(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(False)).first()
    if not image or not image.hashes or not image.image_metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    response = _image_response(image)
    return JSONResponse(
        content=response.model_dump(mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{image.id}-forensic-profile.json"'},
    )


@router.get("/", response_model=List[ImageResponse])
async def get_images(
    case_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all images (optionally filtered by case)"""
    query = db.query(Image).filter(Image.is_deleted.is_(False))
    
    if case_id:
        query = query.filter(Image.case_id == case_id)
    
    images = query.order_by(Image.uploaded_at.desc()).all()
    
    return [_image_response(image) for image in images if image.hashes and image.image_metadata]


@router.get("/{image_id}/file")
async def get_image_file(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(False)).first()
    if not image:
        return _error("IMAGE_NOT_FOUND", "Image was not found.", status.HTTP_404_NOT_FOUND)
    image_path = storage_service.get(image.storage_path)
    if image_path is None:
        return _error("IMAGE_NOT_FOUND", "Stored image file was not found.", status.HTTP_404_NOT_FOUND)
    return FileResponse(image_path, media_type=image.mime_type, headers={"Content-Disposition": "inline"})


@router.delete("/{image_id}")
async def delete_image(image_id: str, db: Session = Depends(get_db)):
    """Move an image to trash while recording an immutable deletion event."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    if not image.is_deleted:
        deleted_at = datetime.now(timezone.utc)
        image.is_deleted = True
        image.deleted_at = deleted_at
        db.add(ImageDeletionAudit(
            image_id=image.id,
            filename=image.original_filename,
            storage_key=image.storage_path,
            sha256=image.hashes.sha256 if image.hashes else None,
            action="SOFT_DELETE",
            occurred_at=deleted_at,
        ))
        db.commit()
    return {"id": image.id, "isDeleted": True, "deletedAt": image.deleted_at}


@router.post("/trash/{image_id}/restore", response_model=ImageResponse)
async def restore_image(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(True)).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trashed image not found")
    image.is_deleted = False
    image.deleted_at = None
    db.commit()
    db.refresh(image)
    return _image_response(image)


@router.delete("/trash/{image_id}")
async def hard_delete_image(image_id: str, db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.is_deleted.is_(True)).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trashed image not found")
    try:
        _hard_delete_image(db, image)
    except Exception as exc:
        logger.exception("image_hard_delete image_id=%s failed", image_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Hard delete failed") from exc
    return {"id": image_id, "status": "HARD_DELETED"}


@router.delete("/trash/empty/all")
async def empty_trash(db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.is_deleted.is_(True)).all()
    deleted = []
    failed = []
    for image in images:
        image_id = image.id
        try:
            _hard_delete_image(db, image)
            deleted.append(image_id)
        except Exception as exc:
            logger.exception("image_hard_delete image_id=%s failed", image_id)
            failed.append({"id": image_id, "message": "Hard delete failed."})
            db.rollback()
    return {"deleted": deleted, "failed": failed}


@router.get("/deletion-audit/{image_id}", response_model=List[DeletionAuditResponse])
async def get_deletion_audit(image_id: str, db: Session = Depends(get_db)):
    entries = db.query(ImageDeletionAudit).filter(
        ImageDeletionAudit.image_id == image_id,
    ).order_by(ImageDeletionAudit.occurred_at.asc()).all()
    return [
        DeletionAuditResponse(
            id=entry.id,
            imageId=entry.image_id,
            filename=entry.filename,
            sha256=entry.sha256,
            action=entry.action,
            occurredAt=entry.occurred_at.replace(tzinfo=timezone.utc)
            if entry.occurred_at.tzinfo is None else entry.occurred_at,
        )
        for entry in entries
    ]
