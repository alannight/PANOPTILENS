"""Extract normalized and raw EXIF metadata without altering source bytes."""

import logging
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image

logger = logging.getLogger(__name__)


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
    if reference == negative_ref:
        result = -result
    elif reference != positive_ref:
        raise ValueError("Missing or invalid GPS reference")
    return result


class MetadataExtractor:
    @staticmethod
    def extract_exif(image_path: str | Path) -> dict[str, Any]:
        try:
            with Image.open(image_path) as image:
                exif = image.getexif()
                top_level = {ExifTags.TAGS.get(tag, str(tag)): value for tag, value in exif.items()}
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif) if exif else {}
                exif_fields = {ExifTags.TAGS.get(tag, str(tag)): value for tag, value in exif_ifd.items()}
                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo) if exif and ExifTags.IFD.GPSInfo in exif else {}
                gps_fields = {ExifTags.GPSTAGS.get(tag, str(tag)): value for tag, value in gps_ifd.items()}
                fields = {**top_level, **exif_fields}
                raw = {
                    **{key: _json_value(value) for key, value in fields.items()},
                    "GPSInfo": {key: _json_value(value) for key, value in gps_fields.items()} if gps_fields else {},
                }

                gps, gps_status = MetadataExtractor._extract_gps(gps_fields)
                return {
                    "status": "PRESENT" if exif else "NOT_PRESENT",
                    "gpsStatus": gps_status,
                    "raw": raw,
                    "camera": {
                        "make": fields.get("Make"),
                        "model": fields.get("Model"),
                        "lens": fields.get("LensModel"),
                        "software": fields.get("Software"),
                    },
                    "capture": {
                        "dateTimeOriginal": fields.get("DateTimeOriginal"),
                        "createDate": fields.get("DateTime"),
                        "modifyDate": fields.get("DateTime"),
                        "dateTimeDigitized": fields.get("DateTimeDigitized"),
                    },
                    "geographic": gps,
                    "image": {
                        "width": image.width,
                        "height": image.height,
                        "orientation": fields.get("Orientation"),
                        "colorSpace": fields.get("ColorSpace"),
                        "resolution": _json_value(fields.get("XResolution")),
                        "format": image.format,
                        "mode": image.mode,
                    },
                }
        except Exception:
            logger.exception("EXIF extraction failed for image %s", Path(image_path).name)
            return MetadataExtractor._empty_metadata("FAILED")

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
            "camera": {"make": None, "model": None, "lens": None, "software": None},
            "capture": {
                "dateTimeOriginal": None,
                "createDate": None,
                "modifyDate": None,
                "dateTimeDigitized": None,
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