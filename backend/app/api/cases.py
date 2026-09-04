from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from app.schemas.case import CaseCreate, CaseResponse

router = APIRouter()


@router.post("/", response_model=CaseResponse)
async def create_case(case: CaseCreate):
    """Create a new investigation case"""
    # In a real implementation, this would save to database
    return CaseResponse(
        id="PL-2026-001",
        name=case.name,
        description=case.description,
        status="ACTIVE",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )


@router.get("/", response_model=List[CaseResponse])
async def list_cases():
    """List all cases"""
    # In a real implementation, this would query database
    return []


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str):
    """Get case details"""
    # Demo implementation
    if case_id == "PL-2026-001":
        return CaseResponse(
            id="PL-2026-001",
            name="Demo Case",
            description="Demo investigation case",
            status="ACTIVE",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Case not found"
    )
