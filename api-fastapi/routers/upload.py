import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.job import JobStatus
from services.job_service import job_service
from services.storage_service import storage_service
from services.queue_service import queue_service

router = APIRouter()


@router.post("/upload")
async def upload_file(
    operation: str = Form(...),
    files: List[UploadFile] = File(...),
    password: Optional[str] = Form(None),
    rotation: Optional[int] = Form(90),
    page_order: Optional[str] = Form(None),
    compression_level: Optional[str] = Form("medium"),
    watermark_text: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    استلام الملفات، التحقق من سلامتها وحجمها، تسجيل المهمة في قاعدة البيانات،
    ثم إرسال بيانات المهمة إلى طابور Redis للـ Worker.
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="المرجو اختيار ملف واحد على الأقل.")

    if len(files) > settings.MAX_FILES_PER_JOB:
        raise HTTPException(
            status_code=400,
            detail=f"تم تجاوز الحد الأقصى للملفات المسموح بها ({settings.MAX_FILES_PER_JOB})."
        )

    try:
        norm_op = storage_service.normalize_operation(operation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job_id = str(uuid.uuid4())
    upload_dir = storage_service.get_job_upload_dir(job_id)
    saved_metadata = []

    for f in files:
        safe_name = storage_service.sanitize_filename(f.filename or "file.pdf")
        dest_path = upload_dir / safe_name
        content = await f.read()

        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"الملف {safe_name} يتجاوز الحد الأقصى المسموح للحجم."
            )

        is_pdf = norm_op != "jpg_to_pdf"
        if not storage_service.validate_magic_bytes(content, is_pdf=is_pdf):
            raise HTTPException(
                status_code=400,
                detail=f"صيغة الملف غير صالحة أو تالفة: {safe_name}"
            )

        with open(dest_path, "wb") as buffer:
            buffer.write(content)

        saved_metadata.append({
            "original_name": f.filename,
            "stored_name": safe_name,
            "size": len(content),
            "path": str(dest_path)
        })

    # تسجيل المهمة رسمياً في قاعدة البيانات بحالة PENDING
    job = await job_service.create_job(db, job_id, norm_op, saved_metadata)

    # تجهيز حمولة الـ Redis الموحدة
    job_payload = {
        "job_id": job_id,
        "operation": norm_op,
        "input_files": saved_metadata,
        "options": {
            "password": password,
            "rotation": rotation,
            "page_order": page_order,
            "compression_level": compression_level,
            "watermark_text": watermark_text
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # دفع المهمة إلى طابور Redis
    enqueued = await queue_service.enqueue_job(job_payload)
    if not enqueued:
        await job_service.update_job_status(
            db,
            job_id,
            JobStatus.FAILED,
            error="تعذر الاتصال بطابور المهام (Redis Broker)."
        )
        raise HTTPException(status_code=503, detail="خدمة طابور المعالجة غير متاحة حالياً.")

    return {
        "success": True,
        "job_id": job.job_id,
        "status": job.status.value,
        "operation": job.operation,
        "files": saved_metadata
    }
