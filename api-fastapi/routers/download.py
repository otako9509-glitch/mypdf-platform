from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import storage_service


router = APIRouter()


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a processed output file.
    """
    outputs_path = "C:\\Users\\ADIL\\Documents\\pj\\storage\\outputs"
    file_path = os.path.join(outputs_path, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )
