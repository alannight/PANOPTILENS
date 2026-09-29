"""Validation helpers for untrusted uploaded image files."""

import os
import warnings
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "40000000"))
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

SIGNATURES = {
    "JPEG": lambda header: header.startswith(b"\xff\xd8\xff"),
    "PNG": lambda header: header.startswith(b"\x89PNG\r\n\x1a\n"),
    "WEBP": lambda header: len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP",
    "GIF": lambda header: header[:6] in (b"GIF87a", b"GIF89a"),
}

EXTENSION_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".gif": "GIF",
}


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def detect_format(header: bytes) -> str:
    for image_format, signature_check in SIGNATURES.items():
        if signature_check(header):
            return image_format
    raise ImageValidationError("UNSUPPORTED_FORMAT", "The uploaded file format is not supported.")


def validate_and_inspect(path: Path, filename: str) -> dict[str, Any]:
    with path.open("rb") as source:
        detected_format = detect_format(source.read(12))

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if image.format != detected_format:
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
                    "mime_type": Image.MIME.get(detected_format, "application/octet-stream"),
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