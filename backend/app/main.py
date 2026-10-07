from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import images, cases, metadata, forensics

# Create FastAPI app
app = FastAPI(
    title="PANOPTILENS API",
    description="Photo Forensics & OSINT Intelligence Platform API",
    version="0.1.0",
)

# CORS Configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
lan_origin_regex = (
    r"^https?://(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=lan_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Include routers
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(metadata.router, prefix="/api/metadata", tags=["metadata"])
app.include_router(forensics.router, prefix="/api/forensics", tags=["forensics"])


@app.get("/")
async def root():
    return {
        "name": "PANOPTILENS API",
        "version": "0.1.0",
        "description": "Photo Forensics & OSINT Intelligence Platform",
        "tagline": "See Beyond The Image",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
