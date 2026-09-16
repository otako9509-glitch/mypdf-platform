from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from services.job_service import job_service

router = APIRouter()


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str, db: AsyncSession = Depends(get_db)):
    """
    تنزيل الملف الناتج من المجلد الخاص بالمهمة مع الحماية من Path Traversal.
    """
    job = await job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة.")

    # تنظيف وتأمين المدخلات
    clean_job_id = Path(job_id).name
    clean_filename = Path(filename).name

    target_file = (settings.OUTPUTS_PATH / clean_job_id / clean_filename).resolve()
    base_output_dir = settings.OUTPUTS_PATH.resolve()

    # التحقق الأمني: منع الخروج من مجلد outputs
    if not str(target_file).startswith(str(base_output_dir)):
        raise HTTPException(status_code=403, detail="طلب غير مصرح به.")

    if not target_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="الملف المطلوب غير متوفر أو تم حذفه لانتهاء المهلة."
        )

    # تحديد نوع الملف
    media_type = "application/pdf" if target_file.suffix.lower() == ".pdf" else "application/octet-stream"

    return FileResponse(
        path=target_file,
        filename=clean_filename,
        media_type=media_type
    )
