from fastapi import APIRouter, HTTPException, status
from app.schemas.image import ImageMetadata

router = APIRouter()


@router.get("/{image_id}", response_model=ImageMetadata)
async def get_metadata(image_id: str):
    """Get metadata for an image"""
    # In a real implementation, this would query database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Metadata not found"
    )
