# PANOPTILENS

**Photo Forensics & OSINT Intelligence Platform**

> **SEE BEYOND THE IMAGE**
> 
> *One Image. Multiple Perspectives. Countless Clues.*

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Status](https://img.shields.io/badge/status-development-yellow)

## Overview

PANOPTILENS is a professional digital forensics and OSINT intelligence platform inspired by **Argus Panoptes**, the many-eyed watcher from Greek mythology. The application analyzes uploaded images from multiple perspectives to extract metadata, forensic evidence, and investigation clues.

### Core Philosophy

A photograph is not just an image. It is a collection of data, clues, relationships, and evidence. PANOPTILENS uses its "many eyes" to examine those perspectives systematically.

**Analysis Flow:**

```
IMAGE
  → OBSERVATION
    → METADATA
      → CLUE
        → RESEARCH
          → CORRELATION
            → EVIDENCE
              → FINDING
```

## Features

### Phase 1 (Current - v0.1)

- ✅ **Professional forensic UI** with dark theme
- ✅ **Case management** system
- ✅ **Image upload** with drag-and-drop
- ✅ **File analysis** with cryptographic hashing (MD5, SHA-1, SHA-256, SHA-512)
- ✅ **EXIF metadata extraction** and display
- ✅ **GPS detection** and geographic data
- ✅ **Privacy warnings** for sensitive metadata
- ✅ **Demo data** for testing and preview

### Phase 2 (Upcoming)

- 🔄 OCR text extraction
- 🔄 Visual clue identification
- 🔄 Clue management system

### Phase 3-5 (Planned)

- 📋 OSINT research integration
- 📋 Evidence repository
- 📋 Knowledge graph visualization
- 📋 Timeline construction
- 📋 Report generation
- 📋 Metadata sanitization

## Tech Stack

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Backend (Planned)
- **Python 3.11+**
- **FastAPI** - API framework
- **PostgreSQL** - Database
- **Redis** - Caching and job queue

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+ (for backend)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PANOPTILENS
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
PANOPTILENS/
├── frontend/
│   ├── app/                  # Next.js app directory
│   │   ├── page.tsx         # Overview dashboard
│   │   ├── images/          # Image management
│   │   ├── metadata/        # Metadata viewer
│   │   ├── forensics/       # Forensic analysis
│   │   ├── clues/           # Clue management
│   │   ├── recon/           # OSINT research
│   │   ├── graph/           # Knowledge graph
│   │   ├── timeline/        # Timeline view
│   │   ├── evidence/        # Evidence repository
│   │   ├── reports/         # Report generator
│   │   └── settings/        # Settings
│   ├── components/          # Reusable UI components
│   ├── features/            # Feature-specific components
│   │   └── images/          # Image analysis features
│   ├── lib/                 # Utilities
│   └── public/              # Static assets
└── backend/                 # Python backend (upcoming)
```

## Navigation

- **Overview** - Intelligence dashboard with case summary
- **Images** - Upload and manage images
- **Metadata** - Detailed EXIF and metadata analysis
- **Forensics** - File structure and cryptographic analysis
- **Clues** - Investigation clue management
- **Recon** - OSINT research interface
- **Graph** - Knowledge graph visualization
- **Timeline** - Chronological event timeline
- **Evidence** - Evidence repository
- **Reports** - Investigation report generation
- **Settings** - Application settings

## Design Principles

### Visual Identity

- **Dark forensic theme** - Professional intelligence interface
- **Restrained accent colors** - Amber/red for emphasis
- **Technical typography** - Monospace for hashes, coordinates, timestamps
- **Subtle Greek mythology motif** - "Many eyes" concept
- **No cliché imagery** - Avoiding generic cybersecurity aesthetics

### Information Architecture

Every finding must include:
- **Source attribution** - Where did this data come from?
- **Confidence levels** - How certain are we?
- **Evidence chain** - What supports this conclusion?
- **Limitations** - What can't we verify?

## Security & Privacy

- Treats uploaded images as untrusted input
- File size limits and validation
- Cryptographic hashing for integrity
- Privacy risk detection
- Optional metadata sanitization
- No automatic overwriting of originals

## Important Notes

⚠️ **This is v0.1 - Demo Version**
- Uses demo data for preview
- OSINT features not yet implemented
- Backend API in development
- Database integration pending

⚠️ **Privacy Notice**
- This tool can expose sensitive metadata
- Always review privacy warnings
- Use metadata sanitization when sharing images

⚠️ **Legal Use Only**
- For lawful investigation and digital forensics
- No unauthorized access or exploitation
- Respect privacy and legal boundaries

## License

This project is for educational and professional use in digital forensics and OSINT investigation.

## Acknowledgments

Inspired by:
- **Argus Panoptes** - Greek mythology's all-seeing guardian
- Professional DFIR (Digital Forensics & Incident Response) tools
- Intelligence analysis platforms
- OSINT investigation methodologies

---

**PANOPTILENS** - *See Beyond The Image*
