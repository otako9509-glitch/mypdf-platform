import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from config import settings

router = APIRouter()

@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    تحميل الملف المعالج والناتج
    """
    # قراءة الملف من مجلد outputs المحدد في الإعدادات
    file_path = os.path.join(settings.OUTPUTS_PATH, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="الملف غير موجود أو انتهت صلاحيته")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )
