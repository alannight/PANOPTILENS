# PANOPTILENS Backend

FastAPI backend for the PANOPTILENS Photo Forensics & OSINT Intelligence Platform.

## Features

- **Image Upload & Processing** - Secure file upload with validation
- **Metadata Extraction** - EXIF, GPS, camera information extraction
- **Cryptographic Hashing** - MD5, SHA-1, SHA-256, SHA-512 calculation
- **Forensic Analysis** - File integrity and anomaly detection
- **Case Management** - Investigation case organization
- **REST API** - Clean, documented API endpoints

## Setup

### Prerequisites

- Python 3.11+
- pip or pipenv
- PostgreSQL (optional, for production)

### Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Create upload directory**
   ```bash
   mkdir uploads
   ```

### Running

**Development Server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

### Images

- `POST /api/images/upload` - Upload and analyze an image
- `GET /api/images/{image_id}` - Get image details
- `DELETE /api/images/{image_id}` - Delete an image

### Cases

- `POST /api/cases/` - Create a new case
- `GET /api/cases/` - List all cases
- `GET /api/cases/{case_id}` - Get case details

### Metadata

- `GET /api/metadata/{image_id}` - Get image metadata

### Forensics

- `GET /api/forensics/{image_id}` - Get forensic analysis

## Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── images.py     # Image upload & management
│   │   ├── cases.py      # Case management
│   │   ├── metadata.py   # Metadata endpoints
│   │   └── forensics.py  # Forensic analysis
│   ├── models/           # Database models (SQLAlchemy)
│   ├── schemas/          # Pydantic schemas
│   │   ├── image.py      # Image-related schemas
│   │   └── case.py       # Case-related schemas
│   ├── services/         # Business logic
│   │   ├── metadata_extractor.py  # EXIF extraction
│   │   └── hash_calculator.py     # Cryptographic hashing
│   ├── workers/          # Background job workers
│   └── main.py           # FastAPI application
├── tests/                # Test files
├── uploads/              # Uploaded files (gitignored)
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Security Features

- **File Validation** - Extension and MIME type checking
- **Size Limits** - Configurable maximum file size
- **Unique Filenames** - UUID-based naming to prevent conflicts
- **CORS Protection** - Configurable allowed origins
- **Input Sanitization** - Pydantic validation on all inputs

## Configuration

Key environment variables in `.env`:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/panoptilens
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=./uploads
```

## Development

**Run tests**
```bash
pytest
```

**Code formatting**
```bash
black app/
```

**Type checking**
```bash
mypy app/
```

## Metadata Extraction

The metadata extractor supports:

- Camera make and model
- Lens information
- Capture timestamps
- GPS coordinates (latitude, longitude, altitude)
- Image dimensions and properties
- Color space and resolution
- Software information

## Hash Calculation

Supports multiple hash algorithms:
- MD5 (legacy, for compatibility)
- SHA-1 (legacy, for compatibility)
- SHA-256 (recommended)
- SHA-512 (maximum security)

## Production Deployment

For production deployment:

1. Use a production WSGI server (Gunicorn + Uvicorn workers)
2. Set up PostgreSQL database
3. Configure Redis for background jobs
4. Use object storage (S3, MinIO) instead of local filesystem
5. Enable HTTPS
6. Set up monitoring and logging
7. Configure backup procedures

## License

Part of the PANOPTILENS project.
