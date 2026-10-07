# PANOPTILENS Backend

FastAPI backend for the Phase 1 image-processing workflow. This is a development prototype, not a production evidence service.

## Implemented Image API

- `POST /api/images/upload` validates JPEG, PNG, WebP, and GIF content, checks Pillow decoding and dimensions, hashes original bytes, extracts EXIF/GPS, and persists image and analysis records.
- `GET /api/images/` lists persisted images.
- `GET /api/images/{image_id}` returns persisted image properties, hashes, metadata, and validation statuses.
- `GET /api/images/{image_id}/file` serves the stored original after looking up the image record.
- `DELETE /api/images/{image_id}` removes the record and attempts storage cleanup.

Case routes are demo stubs. The separate metadata and forensics routes currently return not-found responses; their models/data appear in the image detail response instead. OCR, OSINT, background jobs, evidence workflows, and case authorization are not implemented.

## Local Development

Requirements: Python and a local PostgreSQL database.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `DATABASE_URL`, keep `APP_ENV=development` only on a trusted machine/private LAN, then apply migrations and run the API:

```bash
./venv/bin/alembic upgrade head
fastapi dev app/main.py --host 0.0.0.0
```

The `--host 0.0.0.0` option is required for LAN access. Interactive API docs are available at `http://localhost:8000/docs`; allow TCP port 8000 through the host firewall when needed.

## Configuration and Safety

- `MAX_UPLOAD_SIZE` defaults to 100 MiB and is enforced while streaming into temporary staging.
- `MAX_IMAGE_PIXELS` defaults to 40 million decoded pixels.
- Set `ADMIN_PASSWORD` to a strong secret to authorize image deletion. If unset, the development fallback is `Admin1234`; change the fallback by setting the environment variable before exposing the service, even on a private LAN.
- File format is detected from content signatures and full decoding; browser MIME is not authoritative. HEIF/HEIC uses Pillow-HEIF. DNG/CR2/NEF/ARW additionally require camera metadata and successful LibRaw decoding.
- Hashes are calculated from original upload bytes. Original files are stored locally under UUID-based names.
- EXIF presence and hashes do not prove image authenticity. Metadata consistency is not assessed.

Image endpoints deliberately fail closed outside `APP_ENV=development` because authentication and per-user authorization are not implemented. Development mode is unauthenticated: use this network binding only on a trusted private LAN, and never forward the port to the internet. Uploaded files are not mounted as a public static directory.

## Tests

```bash
./venv/bin/python -m pytest -q
```

Tests use synthetic images and a temporary SQLite database. See the root [TESTING_GUIDE.md](../TESTING_GUIDE.md) for coverage and frontend checks. Root [GETTING_STARTED.md](../GETTING_STARTED.md) describes running the full application.
