# PANOPTILENS Testing Guide

## Automated Backend Tests

The tests create synthetic JPEG/PNG/WebP/GIF images in memory and use a temporary SQLite database and upload directory. No personal image fixtures are committed.

```bash
cd backend
./venv/bin/python -m pytest -q
```

Coverage includes:

- Supported formats and server-detected MIME types
- Original-byte MD5, SHA-1, SHA-256, and SHA-512 results
- Synthetic EXIF values through upload, database persistence, detail response, and file retrieval
- Signature mismatch, corrupt/empty images, oversized files, and unsafe pixel dimensions
- GPS hemisphere conversion and coordinate range rejection
- Production-mode image API fail-closed behavior

## Frontend Checks

```bash
cd frontend
npm run build
npx tsc --noEmit
```

## Local End-to-End Setup

1. Configure a PostgreSQL database and set `DATABASE_URL` in `backend/.env`.
2. Copy `backend/.env.example` to `backend/.env` and use `APP_ENV=development` only for a local, trusted environment. This enables unauthenticated image API access and is not suitable for deployment.
3. Apply migrations:

   ```bash
   cd backend
   ./venv/bin/alembic upgrade head
   ```

4. Start the API:

   ```bash
   ./venv/bin/uvicorn app.main:app --reload --port 8000
   ```

5. Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`, then start the frontend:

   ```bash
   cd frontend
   npm run dev
   ```

6. Upload a synthetic or non-sensitive image at `/images`. Refresh the page and verify it remains in the gallery. Open its detail page and compare file properties, hashes, and EXIF values with the source file.

`MAX_UPLOAD_SIZE` defaults to 10 MiB and `MAX_IMAGE_PIXELS` defaults to 40 million pixels. The API derives format and MIME type from file content; client-supplied MIME is not authoritative.

## Not Covered / Not Implemented

There are no OCR, OSINT, clue, evidence, graph, timeline, reporting, sanitization, authentication, or authorization tests because those application workflows are not implemented. Image hash and metadata checks do not establish image authenticity or tamper-free provenance.