# PANOPTILENS Project Status

**Updated:** 2026-09-29
**Phase:** Core image upload, validation, hashing, EXIF/GPS extraction, persistence, and detail display
**Status:** Development prototype; not production-ready

## Implemented and Verified

- Next.js 15 frontend builds successfully and loads the image gallery from `GET /api/images/`.
- FastAPI accepts JPEG, PNG, WebP, and GIF based on file signatures, then verifies decoding with Pillow.
- Upload bytes are streamed to staging with a configurable `MAX_UPLOAD_SIZE` limit. Oversized or invalid files are not promoted into permanent storage.
- The original uploaded bytes are preserved and used for MD5, SHA-1, SHA-256, and SHA-512 calculation.
- Pillow extracts image properties, normalized camera/capture fields, GPS when valid, and JSON-safe raw EXIF values.
- Image, hashes, metadata, extraction status, and validation status are stored in SQLAlchemy tables.
- Image list/detail responses are built from database records; original files are served through an ID-checked API endpoint rather than a public static mount.
- Image detail safely displays unavailable metadata. GPS coordinates are not sent to a map service until the user opens the external link.
- Synthetic backend integration tests cover all four accepted formats, known-byte hashes, EXIF persistence, invalid/corrupt/empty/oversized files, unsafe dimensions, GPS sign/range handling, and fail-closed production API access.

## Important Limitations

- Authentication and per-user authorization are not implemented. Image API routes are available only when `APP_ENV=development`; otherwise they return `AUTH_NOT_CONFIGURED`. Do not enable development mode on a network-facing deployment.
- Development uploads currently have `owner_id = NULL`. This is explicitly not an authenticated development user.
- EXIF presence does not prove authenticity. Metadata consistency/tampering analysis is `NOT_ASSESSED`.
- Capture timestamps are preserved as EXIF strings and parsed into database datetime columns when they match the standard EXIF timestamp format. Upload and processing timestamps are stored separately.
- The overview dashboard and several non-image pages still contain static/demo content or empty states.
- OCR, OSINT, clues, evidence workflows, knowledge graph, timeline, reporting, metadata sanitization, Redis workers, and object storage are not implemented.
- Database migrations are configured with Alembic. A disposable SQLite migration chain was exercised; PostgreSQL deployment migration has not been verified in this environment.

## Commands

Frontend:

```bash
cd frontend
npm run build
npx tsc --noEmit
```

Backend:

```bash
cd backend
./venv/bin/python -m pytest -q
```

Apply database migrations with a configured development database:

```bash
cd backend
./venv/bin/alembic upgrade head
```