# PANOPTILENS Testing Guide

## Phase 0 Complete - Database Integration Required for Testing

### What's Been Completed ✓

1. **Backend API Integration**
   - `/api/images/upload` - creates database records (Image, ImageHash, ImageMetadata, ForensicAnalysis)
   - `/api/images/{id}` - retrieves from database with all relationships
   - `/api/images/` - lists images with optional case filtering
   - `/DELETE /api/images/{id}` - removes from storage and database

2. **Frontend Integration**
   - `image-upload.tsx` - uses API client, no client-side processing
   - `image-analysis-view.tsx` - fetches real data via `getImage()`, NO DEMO DATA

3. **Environment Configuration**
   - Backend: CORS fixed, secure SECRET_KEY generated
   - Frontend: `.env.local` created with API_URL
   - Both: `.env.example` files created

4. **Critical Bug Fixed**
   - Removed ALL hardcoded demo data from analysis view
   - Image analysis now displays ONLY real forensic data from database

### Prerequisites for Testing

#### 1. PostgreSQL Setup

The application requires PostgreSQL. Set it up as follows:

```bash
# Install PostgreSQL (if not installed)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql

CREATE DATABASE panoptilens;
CREATE USER panoptilens WITH ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE panoptilens TO panoptilens;
\q
```

**Note:** Change 'password' in both the SQL command and `backend/.env` to a secure password.

#### 2. Initialize Database Tables

```bash
cd backend
./venv/bin/python init_db.py
```

Expected output:
```
Initializing PANOPTILENS database...
Database URL: postgresql://panoptilens:***@localhost:5432/panoptilens
✓ All tables created successfully!

Created tables:
  - users
  - cases
  - images
  - image_hashes
  - image_metadata
  - forensic_analyses
  - evidence_items
  - findings
  - ocr_results
  - clues
  - timeline_events
```

#### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Running the Application

#### Terminal 1: Backend Server

```bash
cd backend
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2: Frontend Dev Server

```bash
cd frontend
npm run dev
```

Expected output:
```
▲ Next.js 14.x.x
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000

✓ Ready in Xs
```

### Test Procedure

#### Test 1: Upload Real Image

1. Open browser to `http://localhost:3000/images`
2. Click "Upload Image" or drag-and-drop a JPEG/PNG file with EXIF data
3. Watch upload progress (should show "Uploading to server...")
4. **VERIFY**: No client-side fake delays or processing stages
5. **VERIFY**: Server returns real response (check Network tab)

**Expected Success**:
- Upload completes within seconds (not fake 2-3 second delays)
- Image appears in gallery with real filename
- No errors in console

#### Test 2: View Real Forensic Analysis

1. Click on the uploaded image thumbnail
2. Navigate to analysis page `/images/{id}`
3. **VERIFY**: Loading spinner appears while fetching
4. **VERIFY**: Page displays REAL data:
   - Actual file hash (not hardcoded demo hash)
   - Real EXIF data (camera make/model from YOUR image)
   - Real GPS coordinates (if image has GPS data)
   - Actual file size and dimensions

**Expected Success**:
- NO "DEMO DATA" badge visible
- Hash values are real SHA-256/MD5/etc from uploaded file
- Metadata matches your actual image file
- GPS map shows correct location (if GPS data exists)

**Expected Failure Modes** (all are valid states):
- "Image not found" - if image_id is invalid
- "Cannot connect to server" - if backend is not running
- Missing GPS data - if image has no GPS EXIF
- Missing camera data - if image has no camera EXIF

#### Test 3: Verify Database Persistence

1. Upload an image and note its ID
2. Refresh the page
3. Image should still appear in gallery
4. Click to view analysis - should show same data
5. Restart backend server
6. Image should STILL be present (persisted in database)

**Database Verification** (optional):
```bash
psql -U panoptilens -d panoptilens -c "SELECT id, filename, size FROM images;"
```

#### Test 4: Error Handling

**Test Invalid File Type**:
1. Try uploading a .txt or .pdf file
2. Should show error: "Unsupported file type"

**Test Oversized File**:
1. Try uploading file > 10MB
2. Should show error: "File size exceeds 10MB limit"

**Test Backend Offline**:
1. Stop backend server
2. Try uploading image
3. Should show: "Cannot connect to server - is the backend running?"

### Known Limitations (Phase 0)

1. **Authentication**: Currently uses `owner_id="system"` - real auth not implemented
2. **OCR**: Not yet implemented - OCR results will be empty
3. **Visual Analysis**: Not yet implemented - no object detection
4. **OSINT**: Not yet implemented - no reverse image search
5. **Timeline**: Basic structure only - not fully functional
6. **Case Management**: Basic CRUD only - no workflow features

### Success Criteria

✅ Phase 0 is successful if:

1. Real image uploads create database records
2. Image analysis page displays ONLY real data from database
3. NO demo/fake data appears anywhere
4. Hash values are cryptographically correct
5. EXIF metadata extraction works for real images
6. GPS coordinates display on map (when present)
7. Frontend-backend communication works via API
8. Database persists data across restarts
9. Error handling works for network/validation failures

### Troubleshooting

**Problem**: "Cannot connect to server"
- Check backend is running on port 8000
- Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Check CORS in `backend/.env`: `ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`

**Problem**: "Image not found" after upload
- Check backend logs for errors
- Verify database connection in backend terminal
- Check `backend/uploads/` directory exists and is writable

**Problem**: PostgreSQL connection failed
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `backend/.env` match PostgreSQL user
- Verify database exists: `psql -U panoptilens -d panoptilens -c "\\dt"`

**Problem**: Frontend shows old demo data
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Check that you're viewing the analysis page for a REAL uploaded image, not a demo ID

### Next Steps (Phase 1)

After Phase 0 testing passes:

1. Implement authentication and user management
2. Add OCR text extraction
3. Implement reverse image search
4. Add visual object detection
5. Build OSINT integration
6. Complete timeline functionality
7. Add reporting and export features
8. Implement collaborative case management

---

## Technical Notes

### Database Schema

**Images Table**:
- `id` (UUID) - primary key
- `filename` - storage key
- `original_filename` - user's original filename
- `size` - file size in bytes
- `mime_type` - image/jpeg, etc.
- `storage_path` - filesystem or S3 key
- `owner_id` - user who uploaded (currently "system")
- `case_id` - optional case association
- `uploaded_at` - timestamp
- `is_processed` - processing status

**Relationships** (1:1):
- Image → ImageHash
- Image → ImageMetadata
- Image → ForensicAnalysis

**Relationships** (1:N):
- Image → OCRResults
- Image → Clues

### API Endpoints

```
POST   /api/images/upload          - Upload image with multipart form
GET    /api/images/{id}            - Get single image with all data
GET    /api/images?case_id={id}   - List images, optionally filtered
DELETE /api/images/{id}            - Delete image and related data
```

### Security

- SECRET_KEY: Generated via `secrets.token_urlsafe(32)`
- Passwords: Not stored in `.env` (in .gitignore)
- CORS: Restricted to localhost during development
- File validation: Extension and MIME type checked
- Size limits: 10MB maximum upload

### File Storage

Currently uses local filesystem (`backend/uploads/`).
Structure: `uploads/{uuid}.{ext}`

Future: Abstracted via StorageService for S3 migration.

---

**Document Version**: 1.0
**Last Updated**: Phase 0 Completion
**Status**: Ready for Testing (pending PostgreSQL setup)
