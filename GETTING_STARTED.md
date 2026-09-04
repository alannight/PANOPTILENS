# PANOPTILENS - Getting Started Guide

## Quick Start

### Prerequisites

- **Node.js 18+** and npm (for frontend)
- **Python 3.11+** and pip (for backend)
- PostgreSQL (optional, for production)

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   ```
   http://localhost:3000
   ```

### Backend Setup (Optional for v0.1)

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create uploads directory**
   ```bash
   mkdir uploads
   ```

5. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

6. **Run development server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **API Documentation**
   ```
   http://localhost:8000/docs
   ```

## Features in v0.1

### ✅ Implemented

- **Professional Forensic UI** - Dark theme with PANOPTILENS branding
- **Sidebar Navigation** - All major modules accessible
- **Overview Dashboard** - Case summary and analysis status
- **Image Upload** - Drag-and-drop with validation
- **File Analysis** - Display file information
- **Cryptographic Hashing** - SHA-256 (frontend), MD5/SHA-1/SHA-256/SHA-512 (backend)
- **Metadata Viewer** - Camera, capture, geographic, image metadata
- **GPS Location Display** - Interactive map with coordinates
- **Forensic Analysis** - File identity and hash display
- **Privacy Warnings** - Detection of sensitive metadata
- **Empty States** - Proper placeholders for all modules

### 🔄 Demo Mode

Currently, the frontend operates with:
- Demo image data with sample EXIF
- Client-side hash calculation
- Simulated metadata extraction
- Static OpenStreetMap integration

### 📋 Coming Soon (Phase 2+)

- OCR text extraction
- Visual clue identification
- OSINT research integration
- Knowledge graph visualization
- Timeline construction
- Evidence repository
- Report generation

## Project Structure

```
PANOPTILENS/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App router pages
│   │   ├── page.tsx        # Overview dashboard
│   │   ├── images/         # Image management
│   │   ├── metadata/       # Metadata viewer
│   │   ├── forensics/      # Forensic analysis
│   │   ├── clues/          # Clue management
│   │   ├── recon/          # OSINT research
│   │   ├── graph/          # Knowledge graph
│   │   ├── timeline/       # Timeline view
│   │   ├── evidence/       # Evidence repository
│   │   ├── reports/        # Report generator
│   │   └── settings/       # Settings
│   ├── components/          # Reusable UI components
│   ├── features/            # Feature-specific components
│   │   └── images/         # Image analysis features
│   └── lib/                # Utility functions
│
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   │   ├── metadata_extractor.py
│   │   │   └── hash_calculator.py
│   │   ├── schemas/        # Pydantic models
│   │   └── main.py         # FastAPI app
│   └── requirements.txt
│
├── README.md               # Project overview
└── GETTING_STARTED.md     # This file
```

## Navigation Guide

### Overview
Intelligence dashboard showing case summary, analysis status, and recent findings.

### Images
Upload images via drag-and-drop. View uploaded images in gallery. Click any image to analyze.

### Image Analysis Page
- **Left**: Image preview with file information
- **Right**: 
  - Forensic analysis (hashes, file identity)
  - GPS location map (if available)
  - Detailed metadata (camera, capture, geographic, image)

### Metadata
Aggregated metadata view across all images (placeholder in v0.1).

### Forensics
Technical forensic analysis interface (placeholder in v0.1).

### Clues
Investigation clue management (placeholder in v0.1).

### Recon
OSINT research interface (placeholder in v0.1).

### Graph
Knowledge graph visualization (placeholder in v0.1).

### Timeline
Chronological event timeline (placeholder in v0.1).

### Evidence
Evidence repository (placeholder in v0.1).

### Reports
Investigation report generation (placeholder in v0.1).

## Design Philosophy

PANOPTILENS follows a **forensic investigation workflow**:

```
IMAGE
  ↓ OBSERVATION
  ↓ METADATA
  ↓ CLUE
  ↓ RESEARCH
  ↓ CORRELATION
  ↓ EVIDENCE
  ↓ FINDING
```

### Key Principles

1. **Source Attribution** - Every finding shows its source
2. **Confidence Levels** - Distinguish facts from inferences
3. **Evidence Chain** - Track what supports each conclusion
4. **Limitations** - Acknowledge what cannot be verified

### UI/UX Guidelines

- **Dark forensic theme** - Professional intelligence interface
- **Restrained accent** - Amber/red for emphasis only
- **Technical precision** - Monospace for hashes, coordinates, timestamps
- **Clear warnings** - Privacy risks and metadata limitations
- **No false certainty** - "Location derived from metadata" not "Photo taken at"

## Security Notes

### File Upload Safety

- File type validation (JPG, PNG, WEBP only)
- MIME type checking
- File size limits (10MB default)
- Unique UUID-based filenames
- Server-side validation

### Privacy Features

- Privacy risk detection for GPS/device metadata
- Warning system for sensitive information
- Optional metadata sanitization (coming soon)
- No automatic overwriting of originals

## Development Tips

### Frontend Development

**Run in development mode**
```bash
cd frontend
npm run dev
```

**Build for production**
```bash
npm run build
npm start
```

**Lint code**
```bash
npm run lint
```

### Backend Development

**Run with auto-reload**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Test API**
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Troubleshooting

### Frontend won't start
- Ensure Node.js 18+ is installed
- Delete `node_modules` and `.next`, then run `npm install`
- Check port 3000 is not in use

### Backend errors
- Ensure Python 3.11+ is installed
- Activate virtual environment
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is not in use

### Image upload fails
- Check file size (max 10MB)
- Verify file type (JPG, PNG, WEBP only)
- Ensure `uploads/` directory exists
- Check backend is running

### Map not displaying
- Check internet connection (uses OpenStreetMap)
- Verify GPS metadata exists in image
- Check browser console for errors

## Next Steps

1. **Upload a test image** with EXIF/GPS metadata
2. **Explore the analysis view** to see metadata extraction
3. **Review the forensic hashes** and file information
4. **Check privacy warnings** for sensitive data
5. **Review the demo data** to understand the full vision

## Contributing

This is a portfolio/demonstration project. Key areas for enhancement:

- Real database integration (PostgreSQL)
- OCR implementation
- OSINT source integration
- Knowledge graph library integration
- Timeline visualization
- Report PDF generation

## Resources

- **Next.js Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Pillow (PIL)**: https://pillow.readthedocs.io
- **EXIF Spec**: https://exiftool.org/TagNames/EXIF.html

## License

Educational and portfolio project for digital forensics and OSINT investigation.

---

**PANOPTILENS v0.1** - *See Beyond The Image*
