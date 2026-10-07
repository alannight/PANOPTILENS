import hashlib
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage, TiffImagePlugin
from pillow_heif import from_pillow
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.api.images import get_geocoding_provider
from app.main import app
from app.models import *  # noqa: F401,F403 - register all SQLAlchemy models
from app.services import image_validation
from app.services.geocoding import GeocodingProvider
from app.services.storage import storage_service


class MockGeocodingProvider(GeocodingProvider):
    def reverse_geocode(self, latitude: float, longitude: float):
        return {
            "country": "Testland",
            "province": "Test Province",
            "city": "Test City",
            "district": "Test District",
            "road": "Test Road",
            "formatted": "Test Road, Test City, Testland",
        }


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
    app.dependency_overrides[get_geocoding_provider] = MockGeocodingProvider
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


def jpeg_with_timezone_exif_bytes():
    image = PILImage.new("RGB", (8, 6), color=(110, 70, 30))
    exif = PILImage.Exif()
    exif[306] = "2026:10:05 10:00:00"
    exif[36867] = "2026:10:05 12:34:56"
    exif[36868] = "2026:10:05 12:35:57"
    exif[36880] = "-04:00"
    exif[36881] = "+05:30"
    exif[36882] = "+02:00"
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


def heic_with_gps_bytes():
    image = PILImage.new("RGB", (8, 6), color=(20, 40, 60))
    exif = PILImage.Exif()
    exif[271] = "APPLE"
    exif[272] = "iPhone Test"
    exif[36867] = "2026:10:05 12:00:00"
    exif[34853] = {
        1: "N",
        2: tuple(TiffImagePlugin.IFDRational(numerator, denominator) for numerator, denominator in ((37, 1), (46, 1), (30, 1))),
        3: "W",
        4: tuple(TiffImagePlugin.IFDRational(numerator, denominator) for numerator, denominator in ((122, 1), (25, 1), (10, 1))),
    }
    heif = from_pillow(image)
    heif.info["exif"] = exif.tobytes()
    output = BytesIO()
    heif.save(output, format="HEIF")
    return output.getvalue()


def dng_like_bytes():
    image = PILImage.new("RGB", (8, 6), color=(45, 90, 135))
    exif = PILImage.Exif()
    exif[271] = "Adobe"
    exif[256] = 8
    exif[257] = 6
    exif[36867] = "2026:10:05 09:30:00"
    exif[50706] = bytes((1, 4, 0, 0))
    output = BytesIO()
    image.save(output, format="TIFF", exif=exif)
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
    assert detail.json()["uploadedAt"]
    assert detail.json()["processedAt"]
    assert detail.json()["metadataExtractedAt"]
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
    assert uploaded["metadata"]["capture"]["dateTimeOriginal"] == "2026-09-29T12:34:56"
    assert uploaded["metadata"]["capture"]["dateTimeDigitized"] == "2026-09-29T12:34:57"
    assert uploaded["metadata"]["capture"]["timezoneUnknown"] is True

    detail = client.get(f"/api/images/{uploaded['id']}").json()
    assert detail["metadata"]["camera"]["make"] == "PANOPTILENS TEST"
    assert detail["metadata"]["capture"]["dateTimeOriginal"] == "2026-09-29T12:34:56"
    assert detail["metadata"]["capture"]["dateTimeDigitized"] == "2026-09-29T12:34:57"


def test_exif_offsets_survive_upload_and_sqlite_detail(client):
    response = client.post(
        "/api/images/upload",
        files={"file": ("timezone.jpg", jpeg_with_timezone_exif_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    capture = response.json()["metadata"]["capture"]

    assert capture["dateTimeOriginal"] == "2026-10-05T12:34:56+05:30"
    assert capture["dateTimeDigitized"] == "2026-10-05T12:35:57+02:00"
    assert capture["createDate"] == "2026-10-05T12:35:57+02:00"
    assert capture["modifyDate"] == "2026-10-05T10:00:00-04:00"
    assert capture["timezoneUnknown"] is False
    assert capture["timezoneUnknowns"] == {
        "capturedAt": False,
        "digitizedAt": False,
        "modifiedAt": False,
    }
    assert capture["serverReceivedAt"].endswith("+00:00")

    detail = client.get(f"/api/images/{response.json()['id']}").json()
    assert detail["metadata"]["capture"]["dateTimeOriginal"] == capture["dateTimeOriginal"]


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
    assert gps["address"]["city"] == "Test City"
    assert gps["address"]["formatted"] == "Test Road, Test City, Testland"

    detail = client.get(f"/api/images/{uploaded['id']}").json()
    assert detail["metadata"]["geographic"] == gps


def test_image_detail_repairs_previously_invalid_gps(client):
    from app.models.image import ImageMetadata

    upload = client.post(
        "/api/images/upload",
        files={"file": ("legacy-gps.jpg", jpeg_with_gps_bytes(), "image/jpeg")},
    )
    assert upload.status_code == 200, upload.text
    image_id = upload.json()["id"]

    session_generator = app.dependency_overrides[get_db]()
    session = next(session_generator)
    try:
        metadata = session.query(ImageMetadata).filter_by(image_id=image_id).one()
        metadata.gps_status = "INVALID"
        metadata.gps_latitude = None
        metadata.gps_longitude = None
        session.commit()
    finally:
        session_generator.close()

    detail = client.get(f"/api/images/{image_id}")

    assert detail.status_code == 200, detail.text
    metadata = detail.json()["metadata"]
    assert metadata["gpsStatus"] == "PRESENT"
    assert metadata["geographic"]["latitude"] == pytest.approx(-6.2029166667)
    assert metadata["geographic"]["longitude"] == pytest.approx(106.8166666667)


def test_exifread_gps_fallback_produces_decimal_coordinates(monkeypatch, tmp_path):
    from app.services.metadata_extractor import MetadataExtractor

    image_path = tmp_path / "fallback.jpg"
    image_path.write_bytes(jpeg_with_exif_bytes())
    tags = {
        "GPS GPSLatitude": SimpleNamespace(values=[(6, 1), (12, 1), (105, 10)]),
        "GPS GPSLatitudeRef": SimpleNamespace(printable="S"),
        "GPS GPSLongitude": SimpleNamespace(values=[(106, 1), (49, 1), (0, 1)]),
        "GPS GPSLongitudeRef": SimpleNamespace(printable="E"),
    }
    monkeypatch.setattr("app.services.metadata_extractor.exifread.process_file", lambda *args, **kwargs: tags)

    metadata = MetadataExtractor.extract_exif(image_path)

    assert metadata["gpsStatus"] == "PRESENT"
    assert metadata["geographic"]["latitude"] == pytest.approx(-6.2029166667)
    assert metadata["geographic"]["longitude"] == pytest.approx(106.8166666667)
    assert metadata["fieldSources"]["gps.coordinates"] == "EXIF:GPSInfo"


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


def test_rejects_script_payload_with_jpeg_extension(client, tmp_path):
    response = client.post(
        "/api/images/upload",
        files={"file": ("payload.jpg", b"import os; os.system('id')\n{\"script\": true}", "image/jpeg")},
    )
    assert response.status_code == 415
    assert response.json()["error"] == "UNSUPPORTED_FORMAT"
    assert list((tmp_path / "uploads" / ".staging").glob("upload-*")) == []


def test_heic_upload_extracts_exif_and_gps(client):
    payload = heic_with_gps_bytes()
    response = client.post(
        "/api/images/upload",
        files={"file": ("iphone.heic", payload, "image/heic")},
    )
    assert response.status_code == 200, response.text
    image = response.json()
    assert image["format"] == "HEIF"
    assert image["metadata"]["camera"]["make"] == "APPLE"
    assert image["metadata"]["geographic"]["latitude"] == pytest.approx(37.775)
    assert image["metadata"]["geographic"]["longitude"] == pytest.approx(-122.4194444444)


def test_dng_requires_camera_metadata_and_successful_raw_decode(client, monkeypatch):
    class FakeRaw:
        sizes = SimpleNamespace(raw_width=8, raw_height=6)
        raw_image_visible = SimpleNamespace(size=10)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def unpack(self):
            return None

    monkeypatch.setattr(image_validation.rawpy, "imread", lambda _path: FakeRaw())
    response = client.post(
        "/api/images/upload",
        files={"file": ("camera.dng", dng_like_bytes(), "image/x-adobe-dng")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["format"] == "DNG"
    assert response.json()["metadata"]["camera"]["make"] == "Adobe"
    assert response.json()["metadata"]["capture"]["dateTimeOriginal"] == "2026-10-05T09:30:00"


def test_raw_metadata_fallback_extracts_exifread_tags(tmp_path, monkeypatch):
    from app.services import metadata_extractor

    raw_file = tmp_path / "camera.dng"
    raw_file.write_bytes(dng_like_bytes())

    def pillow_cannot_decode(*_args, **_kwargs):
        raise OSError("Pillow cannot decode RAW")

    monkeypatch.setattr(metadata_extractor.Image, "open", pillow_cannot_decode)
    result = metadata_extractor.MetadataExtractor.extract_exif(raw_file, raw_file.name)

    assert result["camera"]["make"] == "Adobe"
    assert result["capture"]["dateTimeOriginal"] == "2026:10:05 09:30:00"
    assert result["image"]["mode"] == "RAW"
    assert result["fieldSources"]["capture.datetime_original"] == "EXIF:DateTimeOriginal"


def test_fake_dng_text_is_rejected(client, tmp_path):
    response = client.post(
        "/api/images/upload",
        files={"file": ("payload.dng", b"<?php system('id'); ?>", "image/x-adobe-dng")},
    )
    assert response.status_code == 415
    assert response.json()["error"] == "UNSUPPORTED_FORMAT"
    assert list((tmp_path / "uploads" / ".staging").glob("upload-*")) == []


@pytest.mark.parametrize("extension,make,expected_format", [
    ("nef", "NIKON CORPORATION", "NEF"),
    ("arw", "SONY", "ARW"),
    ("cr2", "Canon", "CR2"),
])
def test_camera_raw_format_routes_require_matching_maker(extension, make, expected_format, tmp_path, monkeypatch):
    class FakeRaw:
        sizes = SimpleNamespace(raw_width=8, raw_height=6)
        raw_image_visible = SimpleNamespace(size=10)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def unpack(self):
            return None

    class FakeTag:
        def __init__(self, value):
            self.printable = str(value)
            self.values = [value]

        def __str__(self):
            return self.printable

    if expected_format == "CR2":
        payload = b"II*\x00\x08\x00\x00\x00CR\x02\x00\x10\x00\x00\x00"
    else:
        payload = b"II*\x00\x08\x00\x00\x00\x00\x00\x00\x00"
    source = tmp_path / f"sample.{extension}"
    source.write_bytes(payload)
    monkeypatch.setattr(image_validation, "_raw_tags", lambda _path: {
        "Image Make": FakeTag(make),
        "Image ImageWidth": FakeTag(8),
        "Image ImageLength": FakeTag(6),
    })
    monkeypatch.setattr(image_validation.rawpy, "imread", lambda _path: FakeRaw())

    inspected = image_validation.validate_and_inspect(source, source.name)

    assert inspected["format"] == expected_format
    assert inspected["extension_match"] is True
    assert inspected["mode"] == "RAW"


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
        "GPSLatitude": ((34, 1), (3, 1), (4555, 100)),
        "GPSLatitudeRef": b"S\x00",
        "GPSLongitude": ((106, 1), (49, 1), (0, 1)),
        "GPSLongitudeRef": b"E",
    })
    assert status == "PRESENT"
    assert gps["latitude"] == pytest.approx(-34.0626527778)
    assert gps["longitude"] == pytest.approx(106.8166666667)

    invalid, invalid_status = MetadataExtractor._extract_gps({
        "GPSLatitude": ((91, 1), (0, 1), (0, 1)),
        "GPSLatitudeRef": "N",
        "GPSLongitude": ((0, 1), (0, 1), (0, 1)),
        "GPSLongitudeRef": "E",
    })
    assert invalid is None
    assert invalid_status == "INVALID"


def test_image_delete_requires_admin_password(client, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "Admin1234")
    upload = client.post(
        "/api/images/upload",
        files={"file": ("delete-me.png", png_bytes(), "image/png")},
    )
    assert upload.status_code == 200, upload.text
    image_id = upload.json()["id"]
    endpoint = f"/api/images/{image_id}"

    assert client.delete(endpoint).status_code == 401
    assert client.delete(endpoint, headers={"X-Admin-Password": "wrong"}).status_code == 401
    assert client.delete(endpoint, headers={"X-Admin-Password": "Admin1234"}).status_code == 200
    assert client.delete("/api/images/trash/empty/all").status_code == 401


def test_capture_timestamps_preserve_offsets_and_event_provenance():
    from app.services.metadata_extractor import capture_timestamps

    timestamps = capture_timestamps({
        "DateTimeOriginal": "2026:10:05 12:34:56",
        "OffsetTimeOriginal": "+05:30",
        "DateTimeDigitized": "2026:10:05 12:35:00",
        "OffsetTimeDigitized": "+02:00",
        "DateTime": "2026:10:05 10:00:00",
        "OffsetTime": "-04:00",
    })

    assert timestamps["capturedAt"] == {
        "value": "2026-10-05T12:34:56+05:30",
        "timezoneUnknown": False,
    }
    assert timestamps["digitizedAt"]["value"] == "2026-10-05T12:35:00+02:00"
    assert timestamps["modifiedAt"]["value"] == "2026-10-05T10:00:00-04:00"


def test_capture_timestamps_do_not_guess_missing_timezone():
    from app.services.metadata_extractor import capture_timestamps

    timestamps = capture_timestamps({"DateTimeOriginal": "2026:10:05 12:34:56"})

    assert timestamps["capturedAt"] == {
        "value": "2026-10-05T12:34:56",
        "timezoneUnknown": True,
    }


def test_cases_bulk_upload_filter_and_export(client):
    case_response = client.post(
        "/api/cases/",
        json={"name": "Case-Alpha", "description": "Bulk evidence test"},
    )
    assert case_response.status_code == 200, case_response.text
    case_id = case_response.json()["id"]

    response = client.post(
        "/api/images/upload/bulk",
        data={"case_id": case_id},
        files=[
            ("files", ("one.png", png_bytes(), "image/png")),
            ("files", ("bad.png", b"not an image", "image/png")),
            ("files", ("two.png", png_bytes(), "image/png")),
        ],
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["results"]) == 2
    assert len(result["errors"]) == 1
    assert all(item["caseId"] == case_id for item in result["results"])

    filtered = client.get(f"/api/images/?case_id={case_id}")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 2
    listed_cases = client.get("/api/cases/").json()
    assert any(item["id"] == case_id and item["name"] == "Case-Alpha" for item in listed_cases)

    case_export = client.get(f"/api/cases/{case_id}/export")
    assert case_export.status_code == 200
    assert len(case_export.json()["images"]) == 2
    image_export = client.get(f"/api/images/{result['results'][0]['id']}/export")
    assert image_export.status_code == 200
    assert image_export.headers["content-disposition"].endswith("-forensic-profile.json\"")


def test_annotations_and_integrity_verification(client, tmp_path):
    upload = client.post(
        "/api/images/upload",
        files={"file": ("integrity.png", png_bytes(), "image/png")},
    )
    image_id = upload.json()["id"]

    update = client.patch(
        f"/api/images/{image_id}/annotations",
        json={"tags": [" suspicious ", "network", "suspicious"], "analystNotes": "[SUSPICIOUS] GPS mismatch"},
    )
    assert update.status_code == 200, update.text
    assert update.json() == {"tags": ["suspicious", "network"], "analystNotes": "[SUSPICIOUS] GPS mismatch"}
    detail = client.get(f"/api/images/{image_id}").json()
    assert detail["tags"] == ["suspicious", "network"]
    assert detail["analystNotes"] == "[SUSPICIOUS] GPS mismatch"

    verified = client.post(f"/api/images/{image_id}/verify-integrity")
    assert verified.status_code == 200
    assert verified.json()["status"] == "VERIFIED"
    stored_file = next((tmp_path / "uploads").glob("*.png"))
    with stored_file.open("r+b") as evidence_file:
        evidence_file.seek(-1, 2)
        original_byte = evidence_file.read(1)
        evidence_file.seek(-1, 2)
        evidence_file.write(bytes([original_byte[0] ^ 1]))
    tampered = client.post(f"/api/images/{image_id}/verify-integrity")
    assert tampered.json()["status"] == "TAMPERED"
    assert tampered.json()["actualSha256"] != tampered.json()["expectedSha256"]


def test_soft_delete_restore_hard_delete_and_audit(client, tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "Admin1234")
    admin_headers = {"X-Admin-Password": "Admin1234"}
    upload = client.post(
        "/api/images/upload",
        files={"file": ("lifecycle.png", png_bytes(), "image/png")},
    )
    image_id = upload.json()["id"]
    stored_file = next((tmp_path / "uploads").glob("*.png"))
    assert stored_file.exists()

    deleted = client.delete(f"/api/images/{image_id}", headers=admin_headers)
    assert deleted.status_code == 200
    assert deleted.json()["isDeleted"] is True
    assert client.get("/api/images/").json() == []
    assert len(client.get("/api/images/trash").json()) == 1
    assert client.get(f"/api/images/{image_id}/file").status_code == 404

    restored = client.post(f"/api/images/trash/{image_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["isDeleted"] is False
    assert len(client.get("/api/images/").json()) == 1

    client.delete(f"/api/images/{image_id}", headers=admin_headers)
    hard_delete = client.delete(f"/api/images/trash/{image_id}", headers=admin_headers)
    assert hard_delete.status_code == 200, hard_delete.text
    assert not stored_file.exists()
    assert client.get(f"/api/images/{image_id}").status_code == 404
    audit = client.get(f"/api/images/deletion-audit/{image_id}")
    assert audit.status_code == 200
    assert [entry["action"] for entry in audit.json()] == ["SOFT_DELETE", "SOFT_DELETE", "HARD_DELETE"]


def test_empty_trash_permanently_removes_files(client, tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "Admin1234")
    admin_headers = {"X-Admin-Password": "Admin1234"}
    upload = client.post(
        "/api/images/upload",
        files={"file": ("trash.png", png_bytes(), "image/png")},
    )
    stored_file = next((tmp_path / "uploads").glob("*.png"))
    client.delete(f"/api/images/{upload.json()['id']}", headers=admin_headers)

    emptied = client.delete("/api/images/trash/empty/all", headers=admin_headers)
    assert emptied.status_code == 200
    assert len(emptied.json()["deleted"]) == 1
    assert emptied.json()["failed"] == []
    assert not stored_file.exists()
    assert client.get("/api/images/trash").json() == []