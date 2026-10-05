from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.api.images import _image_response
from app.database import get_db
from app.models.case import Case, CaseStatus
from app.models.image import Image
from app.schemas.case import CaseCreate, CaseResponse

router = APIRouter()


def _case_response(case: Case) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        status=case.status.value if hasattr(case.status, "value") else case.status,
        createdAt=case.created_at,
        updatedAt=case.updated_at,
    )


@router.post("/", response_model=CaseResponse)
async def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    record = Case(
        name=case.name.strip(),
        description=case.description,
        status=CaseStatus.ACTIVE,
        owner_id=None,
    )
    if not record.name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Case name is required")
    db.add(record)
    db.commit()
    db.refresh(record)
    return _case_response(record)


@router.get("/", response_model=List[CaseResponse])
async def list_cases(db: Session = Depends(get_db)):
    return [_case_response(case) for case in db.query(Case).order_by(Case.created_at.desc()).all()]


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return _case_response(case)


@router.get("/{case_id}/export")
async def export_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    images = db.query(Image).filter(
        Image.case_id == case_id,
        Image.is_deleted.is_(False),
    ).order_by(Image.uploaded_at.asc()).all()
    profile = {
        "case": {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "status": case.status.value if hasattr(case.status, "value") else case.status,
            "createdAt": case.created_at.isoformat(),
            "updatedAt": case.updated_at.isoformat(),
        },
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "images": [
            _image_response(image).model_dump(mode="json")
            for image in images
            if image.hashes and image.image_metadata
        ],
    }
    return JSONResponse(
        content=profile,
        headers={"Content-Disposition": f'attachment; filename="{case.id}-forensic-report.json"'},
    )
