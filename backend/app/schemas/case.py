from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True
