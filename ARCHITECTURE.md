# PANOPTILENS Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        PANOPTILENS                          │
│          Photo Forensics & OSINT Intelligence Platform      │
│                   "See Beyond The Image"                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│      FRONTEND        │◄───────►│      BACKEND         │
│    Next.js 15        │   API   │    FastAPI           │
│    TypeScript        │         │    Python 3.11+      │
│    Tailwind CSS      │         │                      │
└──────────────────────┘         └──────────────────────┘
         │                                 │
         ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐
│   Browser/Client     │         │   PostgreSQL DB      │
│   - Upload images    │         │   (planned)          │
│   - View analysis    │         │                      │
│   - Interact with UI │         │                      │
└──────────────────────┘         └──────────────────────┘
```

---

## Frontend Architecture

```
frontend/
│
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout with sidebar
│   ├── page.tsx                 # Overview dashboard
│   │
│   ├── images/
│   │   ├── page.tsx            # Image list & upload
│   │   └── [id]/
│   │       └── page.tsx        # Image analysis view
│   │
│   ├── metadata/page.tsx        # Metadata aggregation
│   ├── forensics/page.tsx       # Forensic analysis
│   ├── clues/page.tsx          # Clue management
│   ├── recon/page.tsx          # OSINT research
│   ├── graph/page.tsx          # Knowledge graph
│   ├── timeline/page.tsx        # Event timeline
│   ├── evidence/page.tsx        # Evidence repository
│   ├── reports/page.tsx         # Report generation
│   └── settings/page.tsx        # Application settings
│
├── components/                   # Reusable UI components
│   ├── sidebar.tsx              # Main navigation
│   ├── stats-card.tsx           # Metric display
│   ├── analysis-status.tsx      # Module status
│   ├── recent-findings.tsx      # Timeline component
│   ├── empty-state.tsx          # Placeholder component
│   └── location-map.tsx         # GPS visualization
│
├── features/                     # Feature modules
│   └── images/
│       ├── image-upload.tsx     # Upload interface
│       ├── image-gallery.tsx    # Grid display
│       ├── image-analysis-view.tsx  # Analysis container
│       ├── forensic-analysis.tsx    # Hash display
│       └── image-metadata.tsx       # EXIF display
│
└── lib/                         # Utilities
    └── utils.ts                 # Helper functions
```

---

## Backend Architecture

```
backend/
│
├── app/
│   ├── main.py                  # FastAPI application
│   │
│   ├── api/                     # API endpoints
│   │   ├── images.py           # Image upload & management
│   │   ├── cases.py            # Case management
│   │   ├── metadata.py         # Metadata endpoints
│   │   └── forensics.py        # Forensic analysis
│   │
│   ├── services/                # Business logic
│   │   ├── metadata_extractor.py  # EXIF extraction
│   │   └── hash_calculator.py     # Cryptographic hashing
│   │
│   ├── schemas/                 # Pydantic models
│   │   ├── image.py            # Image schemas
│   │   └── case.py             # Case schemas
│   │
│   ├── models/                  # Database models
│   │   └── (to be implemented)
│   │
│   └── workers/                 # Background jobs
│       └── (to be implemented)
│
├── uploads/                     # Uploaded files (gitignored)
└── requirements.txt             # Python dependencies
```

---

## Data Flow

### Image Upload & Analysis

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Upload image
     ▼
┌─────────────────┐
│  Image Upload   │
│  Component      │
└────┬────────────┘
     │ 2. Validate file
     ▼
┌─────────────────┐
│  Frontend       │◄─────── 3. Process
│  Processing     │         (demo mode)
└────┬────────────┘
     │ 4. Calculate hash
     ▼
┌─────────────────┐
│  Image Gallery  │
│  Display        │
└────┬────────────┘
     │ 5. Click to analyze
     ▼
┌─────────────────┐
│  Analysis View  │
│  ┌─────────────┐│
│  │ Image       ││
│  │ Preview     ││
│  └─────────────┘│
│  ┌─────────────┐│
│  │ Forensic    ││
│  │ Analysis    ││
│  └─────────────┘│
│  ┌─────────────┐│
│  │ GPS Map     ││
│  └─────────────┘│
│  ┌─────────────┐│
│  │ Metadata    ││
│  └─────────────┘│
└─────────────────┘
```

### Backend Processing (When Connected)

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │ HTTP POST /api/images/upload
     ▼
┌─────────────────┐
│  API Endpoint   │
│  images.py      │
└────┬────────────┘
     │ 1. Validate
     ▼
┌─────────────────┐
│  Save to Disk   │
│  (uploads/)     │
└────┬────────────┘
     │ 2. File saved
     ▼
┌─────────────────────────────┐
│  Parallel Processing        │
│  ┌────────────┐ ┌─────────┐│
│  │ Hash       │ │ Metadata││
│  │ Calculator │ │Extractor││
│  └─────┬──────┘ └────┬────┘│
│        │             │     │
│        │ MD5         │ EXIF│
│        │ SHA-1       │ GPS │
│        │ SHA-256     │ Time│
│        │ SHA-512     │ Cam │
│        │             │     │
└────────┼─────────────┼─────┘
         │             │
         ▼             ▼
    ┌─────────────────────┐
    │  Build Response     │
    │  - File info        │
    │  - Hashes           │
    │  - Metadata         │
    │  - Timestamps       │
    └─────┬───────────────┘
          │ JSON Response
          ▼
    ┌──────────┐
    │ Frontend │
    │ Display  │
    └──────────┘
```

---

## Component Hierarchy

```
App (layout.tsx)
│
├── Sidebar
│   ├── Logo & Brand
│   ├── Navigation Links
│   └── Case Info
│
└── Main Content Area
    │
    ├── Overview Page
    │   ├── StatsCard (×6)
    │   ├── AnalysisStatus
    │   └── RecentFindings
    │
    ├── Images Page
    │   ├── ImageUpload
    │   └── ImageGallery
    │
    ├── Image Analysis Page
    │   ├── ImagePreview
    │   ├── ForensicAnalysis
    │   ├── LocationMap (if GPS)
    │   └── ImageMetadata
    │       ├── Camera Section
    │       ├── Capture Section
    │       ├── Geographic Section
    │       └── Image Section
    │
    └── Other Pages
        └── EmptyState
```

---

## Technology Stack

### Frontend
```
┌──────────────────────────────────┐
│  Framework: Next.js 15           │
│  Language: TypeScript            │
│  Styling: Tailwind CSS           │
│  Icons: Lucide React             │
│  State: React Hooks              │
│  Routing: App Router             │
└──────────────────────────────────┘
```

### Backend
```
┌──────────────────────────────────┐
│  Framework: FastAPI              │
│  Language: Python 3.11+          │
│  Image: Pillow (PIL)             │
│  EXIF: piexif, exifread          │
│  Validation: Pydantic            │
│  Server: Uvicorn                 │
└──────────────────────────────────┘
```

### Database (Planned)
```
┌──────────────────────────────────┐
│  Primary: PostgreSQL             │
│  ORM: SQLAlchemy                 │
│  Migrations: Alembic             │
│  Cache: Redis (background jobs) │
└──────────────────────────────────┘
```

---

## API Design

### RESTful Endpoints

```
/api/
│
├── /images
│   ├── POST   /upload          # Upload new image
│   ├── GET    /{id}            # Get image details
│   └── DELETE /{id}            # Delete image
│
├── /cases
│   ├── POST   /                # Create case
│   ├── GET    /                # List cases
│   └── GET    /{id}            # Get case details
│
├── /metadata
│   └── GET    /{image_id}      # Get metadata
│
└── /forensics
    └── GET    /{image_id}      # Get forensic analysis
```

### Request/Response Flow

```
Client Request
    │
    ▼
[CORS Middleware]
    │
    ▼
[API Router]
    │
    ▼
[Request Validation] (Pydantic)
    │
    ▼
[Business Logic] (Services)
    │
    ▼
[Response Schema] (Pydantic)
    │
    ▼
Client Response (JSON)
```

---

## Security Architecture

### Input Validation

```
Upload Request
    │
    ├─► File Extension Check (.jpg, .png, .webp)
    │
    ├─► MIME Type Check (image/jpeg, image/png, etc.)
    │
    ├─► File Size Check (max 10MB)
    │
    └─► Content Validation (not executable)
        │
        ▼
    Approved ✓
```

### File Storage

```
Original Filename: "vacation.jpg"
                    │
                    ▼
UUID Generation: "a1b2c3d4-e5f6-..."
                    │
                    ▼
Safe Filename: "a1b2c3d4-e5f6-....jpg"
                    │
                    ▼
Store in: /uploads/a1b2c3d4-e5f6-....jpg
```

---

## Metadata Extraction Process

```
Image File
    │
    ▼
[PIL/Pillow Open]
    │
    ├─► Get EXIF Data
    │   │
    │   ├─► Parse Tags
    │   │
    │   ├─► Extract GPS
    │   │   │
    │   │   ├─► Convert Coordinates
    │   │   └─► Parse Altitude
    │   │
    │   ├─► Camera Info
    │   │   │
    │   │   ├─► Make
    │   │   ├─► Model
    │   │   ├─► Lens
    │   │   └─► Software
    │   │
    │   └─► Timestamps
    │       │
    │       ├─► DateTimeOriginal
    │       ├─► CreateDate
    │       └─► ModifyDate
    │
    └─► Image Properties
        │
        ├─► Dimensions (width × height)
        ├─► Color Space
        ├─► Orientation
        └─► Resolution
```

---

## Hash Calculation Process

```
File (binary)
    │
    ▼
Read in 8KB chunks
    │
    ├─► MD5 Hash Object      ──► hexdigest()
    │
    ├─► SHA-1 Hash Object    ──► hexdigest()
    │
    ├─► SHA-256 Hash Object  ──► hexdigest()
    │
    └─► SHA-512 Hash Object  ──► hexdigest()
        │
        ▼
    Return all hashes as dict
```

---

## Future Architecture (Planned)

### Phase 2-5 Extensions

```
Current System
    │
    ├─► OCR Service (Tesseract)
    │   └─► Text extraction
    │
    ├─► Visual Analysis (OpenCV/TensorFlow)
    │   └─► Object/scene detection
    │
    ├─► OSINT Module
    │   ├─► Public source API integration
    │   └─► Geolocation verification
    │
    ├─► Knowledge Graph (vis.js/D3)
    │   └─► Relationship visualization
    │
    ├─► Timeline Engine
    │   └─► Event correlation
    │
    └─► Report Generator
        └─► PDF export
```

---

## Deployment Architecture (Production)

```
┌─────────────────────────────────────────┐
│           Load Balancer (Nginx)         │
└────┬────────────────────────────────┬───┘
     │                                │
     ▼                                ▼
┌──────────────┐              ┌──────────────┐
│  Frontend    │              │  Backend     │
│  (Next.js)   │              │  (FastAPI)   │
│  Port 3000   │◄────────────►│  Port 8000   │
└──────────────┘              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ PostgreSQL   │
                              │ Database     │
                              └──────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ Redis Cache  │
                              │ & Job Queue  │
                              └──────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ S3/MinIO     │
                              │ Object Store │
                              └──────────────┘
```

---

## Scalability Considerations

### Horizontal Scaling

```
Frontend: Multiple Next.js instances behind load balancer
Backend: Multiple FastAPI workers (Gunicorn + Uvicorn)
Database: Primary + Read replicas
Storage: Distributed object storage
Cache: Redis cluster
```

### Performance Optimizations

- Image processing: Background job queue
- Metadata caching: Redis cache
- Static assets: CDN distribution
- Database: Connection pooling
- API: Response caching

---

**PANOPTILENS v0.1 Architecture**

*Designed for scalability, security, and maintainability*
