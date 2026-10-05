"""Validation helpers for untrusted uploaded image files."""

import os
import warnings
from pathlib import Path
from typing import Any

import exifread
import rawpy
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener


MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "40000000"))
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
register_heif_opener()

SIGNATURES = {
    "JPEG": lambda header: header.startswith(b"\xff\xd8\xff"),
    "PNG": lambda header: header.startswith(b"\x89PNG\r\n\x1a\n"),
    "WEBP": lambda header: len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP",
    "GIF": lambda header: header[:6] in (b"GIF87a", b"GIF89a"),
    "BMP": lambda header: header.startswith(b"BM"),
    "TIFF": lambda header: header.startswith((b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")),
    "AVIF": lambda header: _is_bmff_brand(header, {b"avif", b"avis"}),
    "HEIF": lambda header: _is_bmff_brand(header, {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1"}),
}


def _is_bmff_brand(header: bytes, brands: set[bytes]) -> bool:
    return len(header) >= 12 and header[4:8] == b"ftyp" and header[8:12] in brands

EXTENSION_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".dib": "BMP",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".avif": "AVIF",
    ".avifs": "AVIF",
    ".heic": "HEIF",
    ".heif": "HEIF",
    ".dng": "DNG",
    ".cr2": "CR2",
    ".nef": "NEF",
    ".arw": "ARW",
}

RAW_EXTENSIONS = {".dng": "DNG", ".cr2": "CR2", ".nef": "NEF", ".arw": "ARW"}
RAW_MIME_TYPES = {
    "DNG": "image/x-adobe-dng",
    "CR2": "image/x-canon-cr2",
    "NEF": "image/x-nikon-nef",
    "ARW": "image/x-sony-arw",
    "HEIF": "image/heif",
}


def _raw_tags(path: Path) -> dict[str, Any]:
    with path.open("rb") as source:
        return exifread.process_file(source, details=True, strict=True)


def _raw_format(path: Path, filename: str, detected_format: str) -> str | None:
    extension = Path(filename or "").suffix.lower()
    expected = RAW_EXTENSIONS.get(extension)
    if expected is None:
        return None
    try:
        tags = _raw_tags(path)
    except Exception:
        return None

    make = str(tags.get("Image Make", "")).strip().lower()
    if expected == "CR2":
        with path.open("rb") as source:
            header = source.read(16)
        if detected_format != "CR2" or header[8:12] != b"CR\x02\x00":
            return None
    elif expected == "DNG":
        if detected_format != "TIFF" or not any("DNGVersion" in key or key.endswith("0xC612") for key in tags):
            return None
    elif expected == "NEF":
        if detected_format != "TIFF" or "nikon" not in make:
            return None
    elif expected == "ARW":
        if detected_format != "TIFF" or not any(name in make for name in ("sony", "konica minolta")):
            return None

    width = tags.get("EXIF ExifImageWidth") or tags.get("Image ImageWidth")
    height = tags.get("EXIF ExifImageLength") or tags.get("Image ImageLength")
    try:
        width_value = int(width.values[0])
        height_value = int(height.values[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        return None
    if width_value <= 0 or height_value <= 0 or width_value * height_value > MAX_IMAGE_PIXELS:
        raise ImageValidationError("IMAGE_DIMENSIONS_UNSAFE", "The image dimensions exceed the configured safety limit.")

    try:
        with rawpy.imread(str(path)) as raw:
            sizes = raw.sizes
            raw_width = int(sizes.raw_width)
            raw_height = int(sizes.raw_height)
            if raw_width <= 0 or raw_height <= 0 or raw_width * raw_height > MAX_IMAGE_PIXELS:
                raise ImageValidationError("IMAGE_DIMENSIONS_UNSAFE", "The image dimensions exceed the configured safety limit.")
            raw.unpack()
            pixels = raw.raw_image_visible
            if pixels is None or pixels.size == 0:
                return None
    except ImageValidationError:
        raise
    except Exception:
        return None
    return expected


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def detect_format(header: bytes) -> str:
    if header.startswith(b"II*\x00") and len(header) >= 12 and header[8:12] == b"CR\x02\x00":
        return "CR2"
    for image_format, signature_check in SIGNATURES.items():
        if signature_check(header):
            return image_format
    raise ImageValidationError("UNSUPPORTED_FORMAT", "The uploaded file format is not supported.")


def validate_and_inspect(path: Path, filename: str) -> dict[str, Any]:
    with path.open("rb") as source:
        detected_format = detect_format(source.read(12))

    raw_format = _raw_format(path, filename, detected_format)
    if raw_format:
        tags = _raw_tags(path)
        width = int((tags.get("EXIF ExifImageWidth") or tags.get("Image ImageWidth")).values[0])
        height = int((tags.get("EXIF ExifImageLength") or tags.get("Image ImageLength")).values[0])
        return {
            "format": raw_format,
            "mime_type": RAW_MIME_TYPES[raw_format],
            "width": width,
            "height": height,
            "mode": "RAW",
            "extension_match": True,
        }

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                decoded_format = "HEIF" if image.format in {"HEIF", "HEIC"} else image.format
                if decoded_format != detected_format:
                    raise ImageValidationError("CORRUPTED_IMAGE", "The image signature does not match its decoded format.")
                width, height = image.size
                frame_count = getattr(image, "n_frames", 1)
                if width <= 0 or height <= 0 or width * height * frame_count > MAX_IMAGE_PIXELS:
                    raise ImageValidationError("IMAGE_DIMENSIONS_UNSAFE", "The image dimensions exceed the configured safety limit.")
                image.verify()

            with Image.open(path) as image:
                image.load()
                extension = Path(filename or "").suffix.lower()
                return {
                    "format": detected_format,
                    "mime_type": RAW_MIME_TYPES.get(detected_format, Image.MIME.get(detected_format, "application/octet-stream")),
                    "width": width,
                    "height": height,
                    "mode": image.mode,
                    "extension_match": EXTENSION_FORMATS.get(extension) == detected_format,
                }
    except ImageValidationError:
        raise
    except (Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise ImageValidationError("IMAGE_DIMENSIONS_UNSAFE", "The image dimensions exceed the configured safety limit.") from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ImageValidationError("CORRUPTED_IMAGE", "The uploaded image is corrupted or cannot be decoded.") from None