import hashlib
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage, TiffImagePlugin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import *  # noqa: F401,F403 - register all SQLAlchemy models
from app.services import image_validation
from app.services.storage import storage_service


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(storage_service, "base_path", tmp_path / "uploads")
    monkeypatch.setattr(image_validation, "MAX_IMAGE_PIXELS", 1000)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def png_bytes(exif=None):
    image = PILImage.new("RGB", (12, 8), color=(45, 90, 135))
    output = BytesIO()
    image.save(output, format="PNG", exif=exif or b"")
    return output.getvalue()


def jpeg_with_exif_bytes():
    image = PILImage.new("RGB", (8, 6), color=(110, 70, 30))
    exif = PILImage.Exif()
    exif[271] = "PANOPTILENS TEST"
    exif[272] = "Synthetic Camera"
    exif[36867] = "2026:09:29 12:34:56"
    exif[36868] = "2026:09:29 12:34:57"
    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def jpeg_with_gps_bytes():
    image = PILImage.new("RGB", (8, 6), color=(20, 40, 60))
    exif = PILImage.Exif()
    exif[34853] = {
        1: "S",
        2: tuple(TiffImagePlugin.IFDRational(numerator, denominator) for numerator, denominator in ((6, 1), (12, 1), (105, 10))),
        3: "E",
        4: tuple(TiffImagePlugin.IFDRational(numerator, denominator) for numerator, denominator in ((106, 1), (49, 1), (0, 1))),
    }
    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def test_upload_hash_persistence_and_detail(client):
    payload = png_bytes()
    response = client.post(
        "/api/images/upload",
        files={"file": ("../evidence.png", payload, "text/plain")},
    )
    assert response.status_code == 200, response.text
    uploaded = response.json()
    assert uploaded["filename"] == "evidence.png"
    assert uploaded["format"] == "PNG"
    assert uploaded["type"] == "image/png"
    assert uploaded["hash"]["md5"] == hashlib.md5(payload).hexdigest()
    assert uploaded["hash"]["sha1"] == hashlib.sha1(payload).hexdigest()
    assert uploaded["hash"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert uploaded["hash"]["sha512"] == hashlib.sha512(payload).hexdigest()
    assert uploaded["metadata"]["image"]["width"] == 12
    assert uploaded["metadata"]["geographic"] is None

    detail = client.get(f"/api/images/{uploaded['id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["hash"] == uploaded["hash"]
    assert detail.json()["metadata"]["status"] == "NOT_PRESENT"
    assert detail.json()["forensic"]["image_decoded"] is True
    file_response = client.get(f"/api/images/{uploaded['id']}/file")
    assert file_response.status_code == 200
    assert file_response.content == payload

    listing = client.get("/api/images/")
    assert listing.status_code == 200
    assert [image["id"] for image in listing.json()] == [uploaded["id"]]


def test_real_exif_survives_upload_database_and_detail(client):
    payload = jpeg_with_exif_bytes()
    response = client.post(
        "/api/images/upload",
        files={"file": ("camera.jpg", payload, "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    uploaded = response.json()
    assert uploaded["metadata"]["status"] == "PRESENT"
    assert uploaded["metadata"]["camera"]["make"] == "PANOPTILENS TEST"
    assert uploaded["metadata"]["camera"]["model"] == "Synthetic Camera"
    assert uploaded["metadata"]["capture"]["dateTimeOriginal"] == "2026:09:29 12:34:56"
    assert uploaded["metadata"]["capture"]["dateTimeDigitized"] == "2026:09:29 12:34:57"

    detail = client.get(f"/api/images/{uploaded['id']}").json()
    assert detail["metadata"]["camera"]["make"] == "PANOPTILENS TEST"
    assert detail["metadata"]["capture"]["dateTimeOriginal"] == "2026:09:29 12:34:56"
    assert detail["metadata"]["capture"]["dateTimeDigitized"] == "2026:09:29 12:34:57"


def test_real_gps_exif_survives_upload_and_detail(client):
    response = client.post(
        "/api/images/upload",
        files={"file": ("gps.jpg", jpeg_with_gps_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    uploaded = response.json()
    gps = uploaded["metadata"]["geographic"]
    assert uploaded["metadata"]["gpsStatus"] == "PRESENT"
    assert gps["latitude"] == pytest.approx(-6.2029166667)
    assert gps["longitude"] == pytest.approx(106.8166666667)

    detail = client.get(f"/api/images/{uploaded['id']}").json()
    assert detail["metadata"]["geographic"] == gps


@pytest.mark.parametrize("image_format,filename,mime_type", [
    ("JPEG", "test.jpg", "image/jpeg"),
    ("PNG", "test.png", "image/png"),
    ("WEBP", "test.webp", "image/webp"),
    ("GIF", "test.gif", "image/gif"),
])
def test_supported_image_formats(client, image_format, filename, mime_type):
    image = PILImage.new("RGB", (5, 4), color=(12, 34, 56))
    output = BytesIO()
    image.save(output, format=image_format)
    response = client.post(
        "/api/images/upload",
        files={"file": (filename, output.getvalue(), mime_type)},
    )
    assert response.status_code == 200, response.text
    assert response.json()["format"] == image_format


def test_rejects_empty_and_unsafe_dimensions(client, tmp_path):
    empty = client.post("/api/images/upload", files={"file": ("empty.png", b"", "image/png")})
    assert empty.status_code == 400
    assert empty.json()["error"] == "INVALID_FILE"

    image = PILImage.new("RGB", (40, 40))
    output = BytesIO()
    image.save(output, format="PNG")
    unsafe = client.post("/api/images/upload", files={"file": ("large-dimensions.png", output.getvalue(), "image/png")})
    assert unsafe.status_code == 413
    assert unsafe.json()["error"] == "IMAGE_DIMENSIONS_UNSAFE"
    assert list((tmp_path / "uploads").glob("*.png")) == []


def test_image_api_is_disabled_without_development_identity(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    response = client.get("/api/images/")
    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "AUTH_NOT_CONFIGURED"


def test_rejects_invalid_signature_and_cleans_staging(client, tmp_path):
    response = client.post(
        "/api/images/upload",
        files={"file": ("image.png", b"not an image", "image/png")},
    )
    assert response.status_code == 415
    assert response.json()["error"] == "UNSUPPORTED_FORMAT"
    assert list((tmp_path / "uploads").glob("*.png")) == []


def test_rejects_corrupt_image(client, tmp_path):
    response = client.post(
        "/api/images/upload",
        files={"file": ("corrupt.png", b"\x89PNG\r\n\x1a\ntruncated", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "CORRUPTED_IMAGE"
    assert list((tmp_path / "uploads").glob("*.png")) == []


def test_oversized_file_rejected_before_promotion(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.images.MAX_UPLOAD_SIZE", 32)
    response = client.post(
        "/api/images/upload",
        files={"file": ("large.png", png_bytes(), "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["error"] == "FILE_TOO_LARGE"
    assert list((tmp_path / "uploads").glob("*.png")) == []


def test_gps_signs_and_range():
    from app.services.metadata_extractor import MetadataExtractor

    gps, status = MetadataExtractor._extract_gps({
        "GPSLatitude": ((6, 1), (12, 1), (105, 10)),
        "GPSLatitudeRef": "S",
        "GPSLongitude": ((106, 1), (49, 1), (0, 1)),
        "GPSLongitudeRef": "E",
    })
    assert status == "PRESENT"
    assert gps["latitude"] == pytest.approx(-6.2029166667)
    assert gps["longitude"] == pytest.approx(106.8166666667)

    invalid, invalid_status = MetadataExtractor._extract_gps({
        "GPSLatitude": ((91, 1), (0, 1), (0, 1)),
        "GPSLatitudeRef": "N",
        "GPSLongitude": ((0, 1), (0, 1), (0, 1)),
        "GPSLongitudeRef": "E",
    })
    assert invalid is None
    assert invalid_status == "INVALID"