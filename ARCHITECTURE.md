# PANOPTILENS Architecture

## Implemented Image Path

```text
Browser upload
  -> FastAPI multipart endpoint
  -> bounded stream to temporary staging file
  -> signature detection (JPEG / PNG / WebP / GIF)
  -> Pillow verification, decode, and dimension safety checks
  -> hashes of original staged bytes
  -> raw and normalized EXIF/GPS extraction
  -> UUID-named original promoted into local filesystem storage
  -> SQLAlchemy transaction writes image, hashes, metadata, and validation status
  -> API response built from persisted records
  -> Next.js image detail and persistent gallery
```

An upload error removes its staged file. If database persistence fails after promotion, the promoted file is removed. Deletion commits the database record removal and then attempts file cleanup; failed cleanup is logged and can leave an orphaned file for operator cleanup.

## Components

### Frontend

- Next.js App Router, React, and TypeScript
- `frontend/lib/api-client.ts` provides typed API calls and error parsing.
- `/images` loads saved rows from `GET /api/images/` and submits uploads.
- `/images/[id]` loads persisted image detail and displays hashes, image properties, EXIF, GPS, and actual validation flags.
- The dashboard and non-image investigation pages still contain demo values or empty states.

### Backend

- FastAPI route handlers are in `backend/app/api`.
- `image_validation.py` checks signatures, decoded format, integrity, dimensions, and decompression-bomb limits.
- `hash_calculator.py` hashes exact upload bytes in chunks.
- `metadata_extractor.py` uses Pillow's EXIF interfaces and validates GPS coordinates and hemisphere references.
- `storage.py` writes bounded temporary staging files, then promotes validated bytes to UUID-based names.
- SQLAlchemy models persist image, hash, metadata, GPS, and validation data. Alembic migrations define schema changes.

### Storage and Database

- Files are stored on the local filesystem under `UPLOAD_DIR`.
- PostgreSQL is the configured application database; integration tests use temporary SQLite.
- Original files are served through `GET /api/images/{id}/file`, not a public static directory mount.
- Hashes, metadata, and forensic flags are persisted in related tables.

## Access Control and Trust Boundaries

- Authentication and per-user authorization are not implemented.
- Image endpoints fail closed unless `APP_ENV=development`; local development mode allows unauthenticated access and must not be exposed to a network.
- Development uploads use `owner_id = NULL`; this is not an authenticated user identity.
- Client MIME type is informational only. The server derives type from file bytes and Pillow decoding.
- EXIF presence, calculated hashes, and decode validation do not prove authenticity or tamper-free provenance. Metadata consistency remains `NOT_ASSESSED`.
- GPS is not sent to an external map automatically; the UI requires explicit user navigation.

## Not Implemented

Redis/background workers, authentication, OCR, clue extraction, OSINT, evidence correlation, knowledge graph, timeline intelligence, reporting, metadata sanitization, and object storage are future work.