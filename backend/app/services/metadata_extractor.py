"""Extract normalized and raw EXIF metadata without altering source bytes."""

import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

import exifread
from PIL import ExifTags, Image
from pillow_heif import register_heif_opener

logger = logging.getLogger(__name__)
register_heif_opener()
FILENAME_DATETIME_PATTERNS = (
    re.compile(r"(?:^|[^A-Z0-9])(?:IMG|PXL)[_-](?P<date>20\d{6})[_-](?P<time>\d{6})(?:[^0-9]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[^A-Z0-9])Screenshot[_-](?P<date>20\d{6})[-_](?P<time>\d{6})(?:[^0-9]|$)", re.IGNORECASE),
)


def parse_exif_datetime(value: Any, offset: Any = None) -> datetime | None:
    """Parse EXIF/XMP dates without inventing a timezone when none is supplied."""
    if value is None:
        return None
    value = value.decode("ascii", errors="replace") if isinstance(value, bytes) else str(value)
    value = value.strip()
    if not value:
        return None
    normalized = re.sub(r"^(\d{4}):(\d{2}):(\d{2})(?=\s)", r"\1-\2-\3", value)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if parsed.tzinfo is not None or offset is None:
            return parsed
        offset = offset.decode("ascii", errors="replace") if isinstance(offset, bytes) else str(offset)
        match = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", offset.strip())
        if not match:
            return parsed
        hours, minutes = int(match.group(2)), int(match.group(3))
        if hours > 14 or minutes > 59 or (hours == 14 and minutes != 0):
            return parsed
        sign = 1 if match.group(1) == "+" else -1
        return parsed.replace(tzinfo=timezone(sign * timedelta(hours=hours, minutes=minutes)))
    except (TypeError, ValueError, OverflowError):
        return None


def capture_timestamps(fields: dict[str, Any], xmp: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize the three distinct EXIF time events for persistence and API use."""
    xmp = xmp or {}
    values = {
        "capturedAt": (
            fields.get("DateTimeOriginal") or xmp.get("DateTimeOriginal") or xmp.get("DateCreated"),
            fields.get("OffsetTimeOriginal"),
        ),
        "digitizedAt": (
            fields.get("DateTimeDigitized") or xmp.get("CreateDate"),
            fields.get("OffsetTimeDigitized"),
        ),
        "modifiedAt": (
            fields.get("DateTime") or xmp.get("ModifyDate"),
            fields.get("OffsetTime"),
        ),
    }
    result = {}
    for name, (value, offset) in values.items():
        parsed = parse_exif_datetime(value, offset)
        result[name] = {
            "value": parsed.isoformat() if parsed else None,
            "timezoneUnknown": bool(parsed and parsed.utcoffset() is None),
        }
    return result


def infer_filename_datetime(filename: str) -> dict[str, str] | None:
    """Return a timestamp candidate only for explicit known camera filename patterns."""
    for pattern in FILENAME_DATETIME_PATTERNS:
        match = pattern.search(Path(filename).stem)
        if not match:
            continue
        try:
            parsed = datetime.strptime(match.group("date") + match.group("time"), "%Y%m%d%H%M%S")
        except ValueError:
            return None
        if not datetime(1990, 1, 1) <= parsed <= datetime(datetime.now().year + 1, 1, 1):
            return None
        return {
            "value": parsed.isoformat(sep=" "),
            "source": "FILENAME",
            "status": "INFERRED",
            "pattern": pattern.pattern,
        }
    return None


def _json_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return {"numerator": int(value.numerator), "denominator": int(value.denominator)}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _number(value: Any) -> float:
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return float(Fraction(value.numerator, value.denominator))
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return float(Fraction(value[0], value[1]))
    return float(value)


def _coordinate(values: Any, reference: Any, positive_ref: str, negative_ref: str) -> float:
    if not isinstance(values, (tuple, list)) or len(values) != 3:
        raise ValueError("Malformed GPS coordinate")
    degrees, minutes, seconds = (_number(part) for part in values)
    if not (0 <= minutes < 60 and 0 <= seconds < 60):
        raise ValueError("Malformed GPS coordinate")
    result = degrees + minutes / 60 + seconds / 3600
    if isinstance(reference, bytes):
        reference = reference.decode("ascii", errors="ignore")
    reference = str(reference).strip().strip("\x00").upper()
    if reference == negative_ref:
        result = -result
    elif reference != positive_ref:
        raise ValueError("Missing or invalid GPS reference")
    return result


def _xmp_fields(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    try:
        root = ET.fromstring(value if isinstance(value, (bytes, str)) else bytes(value))
    except (ET.ParseError, TypeError, ValueError):
        return {}
    fields = {}
    for element in root.iter():
        if element.text and element.text.strip():
            fields[element.tag.rsplit("}", 1)[-1].split(":")[-1]] = element.text.strip()
        for key, item in element.attrib.items():
            fields[key.rsplit("}", 1)[-1].split(":")[-1]] = item
    return fields


def _raw_tag_value(tags: dict[str, Any], name: str) -> Any:
    tag = tags.get(name)
    if tag is None:
        return None
    return getattr(tag, "printable", str(tag))


def _extract_exifread_gps(image_path: str | Path) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    try:
        with Path(image_path).open("rb") as source:
            tags = exifread.process_file(source, details=True, strict=False)
    except Exception:
        return None, "NOT_PRESENT", {}

    gps_fields = {
        "GPSLatitude": getattr(tags.get("GPS GPSLatitude"), "values", None),
        "GPSLatitudeRef": _raw_tag_value(tags, "GPS GPSLatitudeRef"),
        "GPSLongitude": getattr(tags.get("GPS GPSLongitude"), "values", None),
        "GPSLongitudeRef": _raw_tag_value(tags, "GPS GPSLongitudeRef"),
        "GPSAltitude": getattr(tags.get("GPS GPSAltitude"), "values", [None])[0],
        "GPSAltitudeRef": _raw_tag_value(tags, "GPS GPSAltitudeRef"),
        "GPSTimeStamp": getattr(tags.get("GPS GPSTimeStamp"), "values", None),
        "GPSImgDirection": getattr(tags.get("GPS GPSImgDirection"), "values", [None])[0],
    }
    gps, status = MetadataExtractor._extract_gps(gps_fields)
    return gps, status, gps_fields


def _extract_raw_metadata(image_path: str | Path, filename: str | None) -> dict[str, Any]:
    with Path(image_path).open("rb") as source:
        tags = exifread.process_file(source, details=True, strict=True)

    fields = {
        "Make": _raw_tag_value(tags, "Image Make"),
        "Model": _raw_tag_value(tags, "Image Model"),
        "LensModel": _raw_tag_value(tags, "EXIF LensModel"),
        "Software": _raw_tag_value(tags, "Image Software"),
        "DateTime": _raw_tag_value(tags, "Image DateTime"),
        "DateTimeOriginal": _raw_tag_value(tags, "EXIF DateTimeOriginal") or _raw_tag_value(tags, "Image DateTimeOriginal"),
        "DateTimeDigitized": _raw_tag_value(tags, "EXIF DateTimeDigitized") or _raw_tag_value(tags, "Image DateTimeDigitized"),
        "OffsetTime": _raw_tag_value(tags, "Image OffsetTime"),
        "OffsetTimeOriginal": _raw_tag_value(tags, "EXIF OffsetTimeOriginal"),
        "OffsetTimeDigitized": _raw_tag_value(tags, "EXIF OffsetTimeDigitized"),
        "Orientation": _raw_tag_value(tags, "Image Orientation"),
        "ColorSpace": _raw_tag_value(tags, "EXIF ColorSpace"),
        "XResolution": _raw_tag_value(tags, "Image XResolution"),
        "YResolution": _raw_tag_value(tags, "Image YResolution"),
        "ResolutionUnit": _raw_tag_value(tags, "Image ResolutionUnit"),
    }
    gps_fields = {
        "GPSLatitude": getattr(tags.get("GPS GPSLatitude"), "values", None),
        "GPSLatitudeRef": _raw_tag_value(tags, "GPS GPSLatitudeRef"),
        "GPSLongitude": getattr(tags.get("GPS GPSLongitude"), "values", None),
        "GPSLongitudeRef": _raw_tag_value(tags, "GPS GPSLongitudeRef"),
        "GPSAltitude": getattr(tags.get("GPS GPSAltitude"), "values", [None])[0],
        "GPSAltitudeRef": getattr(tags.get("GPS GPSAltitudeRef"), "values", [None])[0],
        "GPSTimeStamp": getattr(tags.get("GPS GPSTimeStamp"), "values", None),
        "GPSImgDirection": getattr(tags.get("GPS GPSImgDirection"), "values", [None])[0],
    }
    gps, gps_status = MetadataExtractor._extract_gps(gps_fields)
    make = fields["Make"]
    model = fields["Model"]
    software = fields["Software"]
    capture_original = fields["DateTimeOriginal"]
    capture_digitized = fields["DateTimeDigitized"]
    timestamps = capture_timestamps(fields)
    filename_datetime = infer_filename_datetime(filename or Path(image_path).name)
    raw = {key: _json_value(getattr(tag, "values", tag)) for key, tag in tags.items()}
    raw["GPSInfo"] = {key: _json_value(value) for key, value in gps_fields.items() if value is not None}
    width = _raw_tag_value(tags, "EXIF ExifImageWidth") or _raw_tag_value(tags, "Image ImageWidth")
    height = _raw_tag_value(tags, "EXIF ExifImageLength") or _raw_tag_value(tags, "Image ImageLength")
    try:
        width = int(width) if width is not None else None
        height = int(height) if height is not None else None
    except (TypeError, ValueError):
        width = height = None

    return {
        "status": "PRESENT" if any((make, model, capture_original, gps)) else "PARTIAL" if tags else "NOT_PRESENT",
        "gpsStatus": gps_status,
        "raw": raw,
        "derived": {
            "filenameDateTime": filename_datetime,
            "timestamps": timestamps,
            "fileSystemTimestamps": {},
        },
        "fieldSources": {
            "camera.make": "EXIF:Make" if make else None,
            "camera.model": "EXIF:Model" if model else None,
            "camera.software": "EXIF:Software" if software else None,
            "capture.datetime_original": "EXIF:DateTimeOriginal" if capture_original else None,
            "capture.datetime_digitized": "EXIF:DateTimeDigitized" if capture_digitized else None,
            "camera.lens_model": "EXIF:LensModel" if fields["LensModel"] else None,
            "capture.filename_candidate": "FILENAME" if filename_datetime else None,
            "gps.coordinates": "EXIF:GPSInfo" if gps else None,
        },
        "camera": {"make": make, "model": model, "lens": fields["LensModel"], "software": software},
        "capture": {
            "dateTimeOriginal": capture_original,
            "createDate": capture_digitized,
            "modifyDate": fields["DateTime"],
            "dateTimeDigitized": capture_digitized,
            "offsetTimeOriginal": fields["OffsetTimeOriginal"],
            "offsetTimeDigitized": fields["OffsetTimeDigitized"],
            "offsetTime": fields["OffsetTime"],
        },
        "geographic": gps,
        "image": {
            "width": width,
            "height": height,
            "orientation": fields["Orientation"],
            "colorSpace": fields["ColorSpace"],
            "resolution": None,
            "format": Path(image_path).suffix.upper().lstrip("."),
            "mode": "RAW",
        },
    }


class MetadataExtractor:
    @staticmethod
    def extract_exif(image_path: str | Path, filename: str | None = None) -> dict[str, Any]:
        try:
            with Image.open(image_path) as image:
                exif = image.getexif()
                top_level = {ExifTags.TAGS.get(tag, str(tag)): value for tag, value in exif.items()}
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif) if exif else {}
                exif_fields = {ExifTags.TAGS.get(tag, str(tag)): value for tag, value in exif_ifd.items()}
                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo) if exif and ExifTags.IFD.GPSInfo in exif else {}
                gps_fields = {ExifTags.GPSTAGS.get(tag, str(tag)): value for tag, value in gps_ifd.items()}
                fields = {**top_level, **exif_fields}
                xmp_raw = image.info.get("XML:com.adobe.xmp") or image.info.get("xmp")
                xmp = _xmp_fields(xmp_raw)
                try:
                    iptc_raw = Image.getiptcinfo(image) or {}
                except (AttributeError, NotImplementedError, OSError, ValueError):
                    iptc_raw = {}
                raw = {
                    **{key: _json_value(value) for key, value in fields.items()},
                    "GPSInfo": {key: _json_value(value) for key, value in gps_fields.items()} if gps_fields else {},
                }
                if xmp_raw:
                    raw["XMP"] = _json_value(xmp_raw)
                if iptc_raw:
                    raw["IPTC"] = {str(key): _json_value(value) for key, value in iptc_raw.items()}
                filename_datetime = infer_filename_datetime(filename or Path(image_path).name)

                gps, gps_status = MetadataExtractor._extract_gps(gps_fields)
                if gps_status != "PRESENT":
                    fallback_gps, fallback_status, fallback_fields = _extract_exifread_gps(image_path)
                    if fallback_status == "PRESENT" or (gps_status == "NOT_PRESENT" and fallback_status == "INVALID"):
                        gps, gps_status = fallback_gps, fallback_status
                        if fallback_fields:
                            raw["GPSInfo"] = {
                                key: _json_value(value)
                                for key, value in fallback_fields.items()
                                if value is not None
                            }
                make = fields.get("Make") or xmp.get("Make")
                model = fields.get("Model") or xmp.get("Model")
                software = fields.get("Software") or xmp.get("Software") or xmp.get("CreatorTool")
                capture_original = fields.get("DateTimeOriginal") or xmp.get("DateTimeOriginal") or xmp.get("DateCreated")
                capture_digitized = fields.get("DateTimeDigitized") or xmp.get("CreateDate")
                timestamps = capture_timestamps(fields, xmp)
                recognized_metadata = bool(fields or gps_fields or xmp or iptc_raw)
                core_metadata = bool(make or model or capture_original)
                if not recognized_metadata:
                    metadata_status = "NOT_PRESENT"
                elif core_metadata:
                    metadata_status = "PRESENT"
                else:
                    metadata_status = "PARTIAL"
                field_sources = {
                    "camera.make": "EXIF:Make" if fields.get("Make") else ("XMP:Make" if xmp.get("Make") else None),
                    "camera.model": "EXIF:Model" if fields.get("Model") else ("XMP:Model" if xmp.get("Model") else None),
                    "camera.software": "EXIF:Software" if fields.get("Software") else ("XMP:CreatorTool" if xmp.get("CreatorTool") else None),
                    "capture.datetime_original": "EXIF:DateTimeOriginal" if fields.get("DateTimeOriginal") else ("XMP:DateTimeOriginal" if xmp.get("DateTimeOriginal") else ("XMP:DateCreated" if xmp.get("DateCreated") else None)),
                    "capture.datetime_digitized": "EXIF:DateTimeDigitized" if fields.get("DateTimeDigitized") else ("XMP:CreateDate" if xmp.get("CreateDate") else None),
                    "camera.lens_model": "EXIF:LensModel" if fields.get("LensModel") else None,
                    "capture.filename_candidate": "FILENAME" if filename_datetime else None,
                    "gps.coordinates": "EXIF:GPSInfo" if gps else None,
                }
                
                offset_time = fields.get("OffsetTime")
                offset_time_original = fields.get("OffsetTimeOriginal")
                offset_time_digitized = fields.get("OffsetTimeDigitized")
                
                file_stat = os.stat(image_path)
                filesystem_timestamps = {
                    "stagedFileCreatedAt": datetime.fromtimestamp(file_stat.st_birthtime, timezone.utc).isoformat()
                    if hasattr(file_stat, "st_birthtime") else None,
                    "stagedFileMetadataChangedAt": datetime.fromtimestamp(file_stat.st_ctime, timezone.utc).isoformat(),
                    "stagedFileModifiedAt": datetime.fromtimestamp(file_stat.st_mtime, timezone.utc).isoformat(),
                }
                resolution = {
                    "x": _json_value(fields.get("XResolution")),
                    "y": _json_value(fields.get("YResolution")),
                    "unit": {2: "inch", 3: "centimeter"}.get(fields.get("ResolutionUnit"), "unknown"),
                } if fields.get("XResolution") is not None or fields.get("YResolution") is not None else None
                return {
                    "status": metadata_status,
                    "gpsStatus": gps_status,
                    "raw": raw,
                    "derived": {
                        "filenameDateTime": filename_datetime,
                        "timestamps": timestamps,
                        "fileSystemTimestamps": filesystem_timestamps,
                    },
                    "fieldSources": field_sources,
                    "camera": {
                        "make": make,
                        "model": model,
                        "lens": fields.get("LensModel"),
                        "software": software,
                    },
                    "capture": {
                        "dateTimeOriginal": capture_original,
                        "createDate": capture_digitized,
                        "modifyDate": fields.get("DateTime") or xmp.get("ModifyDate"),
                        "dateTimeDigitized": capture_digitized,
                        "offsetTimeOriginal": offset_time_original,
                        "offsetTimeDigitized": offset_time_digitized,
                        "offsetTime": offset_time,
                    },
                    "geographic": gps,
                    "image": {
                        "width": image.width,
                        "height": image.height,
                        "orientation": fields.get("Orientation"),
                        "colorSpace": fields.get("ColorSpace"),
                        "resolution": resolution,
                        "format": image.format,
                        "mode": image.mode,
                    },
                }
        except Exception:
            logger.exception("metadata extraction failed for image %s", Path(image_path).name)
            if Path(filename or image_path).suffix.lower() in {".dng", ".cr2", ".nef", ".arw"}:
                try:
                    return _extract_raw_metadata(image_path, filename)
                except Exception:
                    logger.exception("RAW metadata fallback failed for image %s", Path(image_path).name)
            return MetadataExtractor._empty_metadata("UNREADABLE")

    @staticmethod
    def _extract_gps(gps: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        if not gps:
            return None, "NOT_PRESENT"
        try:
            latitude = _coordinate(gps.get("GPSLatitude"), gps.get("GPSLatitudeRef"), "N", "S")
            longitude = _coordinate(gps.get("GPSLongitude"), gps.get("GPSLongitudeRef"), "E", "W")
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("GPS coordinate outside valid range")

            altitude = gps.get("GPSAltitude")
            altitude_value = _number(altitude) if altitude is not None else None
            if altitude_value is not None and gps.get("GPSAltitudeRef") in (1, b"\x01"):
                altitude_value = -altitude_value
            timestamp = gps.get("GPSTimeStamp")
            timestamp_value = ":".join(f"{_number(value):g}" for value in timestamp) if timestamp else None
            direction = gps.get("GPSImgDirection")
            return {
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude_value,
                "gpsTimestamp": timestamp_value,
                "direction": _number(direction) if direction is not None else None,
            }, "PRESENT"
        except (TypeError, ValueError, ZeroDivisionError):
            return None, "INVALID"

    @staticmethod
    def _empty_metadata(status: str) -> dict[str, Any]:
        return {
            "status": status,
            "gpsStatus": "NOT_PRESENT",
            "raw": {},
            "derived": {
                "filenameDateTime": None,
                "timestamps": {
                    "capturedAt": {"value": None, "timezoneUnknown": False},
                    "digitizedAt": {"value": None, "timezoneUnknown": False},
                    "modifiedAt": {"value": None, "timezoneUnknown": False},
                },
                "fileSystemTimestamps": {},
            },
            "fieldSources": {},
            "camera": {"make": None, "model": None, "lens": None, "software": None},
            "capture": {
                "dateTimeOriginal": None,
                "createDate": None,
                "modifyDate": None,
                "dateTimeDigitized": None,
                "offsetTimeOriginal": None,
                "offsetTimeDigitized": None,
                "offsetTime": None,
            },
            "geographic": None,
            "image": {
                "width": None,
                "height": None,
                "orientation": None,
                "colorSpace": None,
                "resolution": None,
                "format": None,
                "mode": None,
            },
        }