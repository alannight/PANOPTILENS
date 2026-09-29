# PANOPTILENS Getting Started

PANOPTILENS is a development prototype. Its implemented workflow is image upload, server-side validation, hashing, EXIF/GPS extraction, database persistence, and image detail display. Image API access has no authentication and is enabled only for explicit local development mode.

## Prerequisites

- Node.js and npm
- Python and pip
- PostgreSQL for local end-to-end persistence

## Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure `DATABASE_URL` for a local PostgreSQL database and keep `APP_ENV=development` only on a trusted local machine. The development mode allows unauthenticated image API access; do not expose it to a network.

Apply schema migrations and start the API:

```bash
./venv/bin/alembic upgrade head
./venv/bin/uvicorn app.main:app --reload --port 8000
```

The interactive API documentation is at `http://localhost:8000/docs`.

## Frontend

```bash
cd frontend
npm install
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`, then:

```bash
npm run dev
```

Open `http://localhost:3000/images` to upload and inspect an image. The gallery reloads persisted images from the API.

## Limits and Data Handling

- `MAX_UPLOAD_SIZE` defaults to 10 MiB. Files are streamed into a staging directory and rejected before permanent storage if they exceed this limit.
- `MAX_IMAGE_PIXELS` defaults to 40 million decoded pixels.
- JPEG, PNG, WebP, and GIF are accepted by content signature and Pillow decode, regardless of the browser-supplied MIME value.
- Hashes are calculated from the original uploaded bytes. Originals are not resized or re-encoded.
- EXIF can be absent or invalid. No EXIF is not an error, and EXIF presence does not prove authenticity.
- GPS is shown only when coordinates are valid. External map navigation requires an explicit click.

## Tests

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for backend integration tests, frontend build/type checks, and known limitations. OCR, OSINT, clues, evidence workflows, graph, timeline, reports, and authentication remain unimplemented.