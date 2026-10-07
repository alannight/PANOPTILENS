# PANOPTILENS

**Photo Forensics & OSINT Intelligence Platform**
*One Image. Multiple Perspectives. Countless Clues.*

PANOPTILENS is a development prototype for examining image files and their embedded metadata. Phase 1 focuses on the core image pipeline; it does not establish image authenticity or metadata integrity.

## Phase 1 Image Pipeline

- Drag-and-drop upload with server-side streaming size limits
- JPEG, PNG, WebP, and GIF content-signature validation and Pillow decoding
- MD5, SHA-1, SHA-256, and SHA-512 over the original uploaded bytes
- Pillow EXIF extraction, JSON-safe raw tags, GPS conversion/range checks, and image properties
- SQLAlchemy persistence with Alembic migrations
- Persistent image gallery, detail API, and ID-checked original-file response
- Null-safe metadata display and user-initiated external map navigation

The backend image API is unauthenticated only in explicit local development mode (`APP_ENV=development`). Outside that mode it fails closed with `AUTH_NOT_CONFIGURED`. Authentication and per-user authorization are not implemented; do not expose development mode to a network.

## Roadmap

OCR, visual clue extraction, OSINT research, case/evidence workflows, correlation, knowledge graph, timeline, reporting, metadata sanitization, Redis workers, and object storage are not implemented.

The overview dashboard still contains demo values. Validation and hashes are useful file-processing results, not proof that an image is authentic or untampered.

## Stack

- Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, Pillow
- Persistence: PostgreSQL, SQLAlchemy, Alembic
- Current file storage: local filesystem

## Local Setup

See [GETTING_STARTED.md](GETTING_STARTED.md) for local setup, [ARCHITECTURE.md](ARCHITECTURE.md) for the implemented pipeline and trust boundaries, and [TESTING_GUIDE.md](TESTING_GUIDE.md) for checks and coverage. Backend-specific setup and API details are in [backend/README.md](backend/README.md).

## Trusted LAN Development

On a trusted private Wi-Fi network, start the backend from `backend/` with `fastapi dev app/main.py --host 0.0.0.0`. The `--host 0.0.0.0` option is required for LAN access. Start the frontend from `frontend/` with `npm run dev -- -p 3000 -H 0.0.0.0`. Open `http://<host-LAN-IP>:3000` on the other device. Next.js proxies API requests to `http://localhost:8000` by default; set `API_PROXY_TARGET` if the backend listens elsewhere. Allow TCP ports 3000 and 8000 through the host firewall as needed.

The backend's development image endpoints are unauthenticated. Use only on a trusted private LAN, and do not forward these ports to the internet.

## Project Map

```text
frontend/  Next.js pages, image UI, API client
backend/   FastAPI routes, image services, SQLAlchemy models, Alembic migrations
```

## Privacy and Legal Use

Images may contain location, camera, and capture-time data. Review metadata before sharing evidence. PANOPTILENS does not currently remove or sanitize metadata. Use the project only for lawful investigation and respect applicable privacy requirements.