from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="PDFFlow API is running",
        version="1.0.0"
    )
