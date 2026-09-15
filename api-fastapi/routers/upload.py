from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import job_service, storage_service, queue_service, JobStatus
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.post("/upload")
async def upload_file(
    operation: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    compression_level: Optional[str] = Form(None),
    rotation_angle: Optional[str] = Form(None),
    split_mode: Optional[str] = Form(None),
    page_range: Optional[str] = Form(None),
    single_page: Optional[str] = Form(None),
    page_order: Optional[str] = Form(None),
    image_quality: Optional[str] = Form(None),
    image_dpi: Optional[str] = Form(None),
    page_orientation: Optional[str] = Form(None),
    page_margin: Optional[str] = Form(None),
    watermark_type: Optional[str] = Form(None),
    watermark_text: Optional[str] = Form(None),
    watermark_opacity: Optional[str] = Form(None),
    watermark_position: Optional[str] = Form(None),
    watermark_rotation: Optional[str] = Form(None),
    watermark_color: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    encryption_level: Optional[str] = Form(None),
    allow_print: Optional[bool] = Form(None),
    allow_copy: Optional[bool] = Form(None),
    allow_modify: Optional[bool] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    # دمج الملفات القادمة سواء سميت file أو files
    uploaded_files: List[UploadFile] = []
    if files:
        uploaded_files.extend(files)
    if file:
        uploaded_files.append(file)

    if not uploaded_files:
        raise HTTPException(status_code=400, detail="لم يتم اختيار أي ملف للرفع.")

    # توحيد صيغة اسم العملية
    norm_operation = operation.replace("-", "_").lower()

    # التحقق من نوع الملفات
    for uf in uploaded_files:
        filename_lower = (uf.filename or "").lower()
        is_pdf = filename_lower.endswith(".pdf")
        is_img = filename_lower.endswith((".jpg", ".jpeg", ".png"))

        if not (is_pdf or is_img):
            raise HTTPException(status_code=400, detail=f"الملف '{uf.filename}' غير مدعوم.")

        # التحقق من ترويسة ملفات الـ PDF
        if is_pdf:
            file_content = await uf.read()
            if not storage_service.validate_pdf_magic_bytes(file_content):
                raise HTTPException(status_code=400, detail=f"الملف '{uf.filename}' ليس ملف PDF صالحاً.")
            await uf.seek(0)

    # إنشاء المهمة
    job = job_service.create_job(operation=norm_operation, input_files=[])

    input_files_metadata = []
    # حفظ الملفات محلياً في مجلد التخزين
    for uf in uploaded_files:
        try:
            file_metadata = storage_service.save_upload_file(uf, job.job_id)
            input_files_metadata.append({
                "original_name": file_metadata["original_name"],
                "stored_name": file_metadata["stored_name"],
                "size": file_metadata["size"]
            })
        except Exception as e:
            job_service.delete_job(job.job_id)
            raise HTTPException(status_code=500, detail=f"تعذر حفظ الملف: {str(e)}")

    # تحديث المهمة بقائمة الملفات
    job_service.update_job_input_files(job.job_id, input_files_metadata)

    # تجهيز كائن المهمة للـ Worker
    job_data = {
        "job_id": job.job_id,
        "operation": norm_operation,
        "input_files": input_files_metadata,
        "compression_level": compression_level,
        "rotation_angle": rotation_angle,
        "split_mode": split_mode,
        "page_range": page_range,
        "single_page": single_page,
        "page_order": page_order,
        "image_quality": image_quality,
        "image_dpi": image_dpi,
        "page_orientation": page_orientation,
        "page_margin": page_margin,
        "watermark_type": watermark_type,
        "watermark_text": watermark_text,
        "watermark_opacity": watermark_opacity,
        "watermark_position": watermark_position,
        "watermark_rotation": watermark_rotation,
        "watermark_color": watermark_color,
        "password": password,
        "encryption_level": encryption_level,
        "allow_print": allow_print,
        "allow_copy": allow_copy,
        "allow_modify": allow_modify
    }

    # محاولة إرسال المهمة إلى Redis مع تحديد timeout بثانية واحدة لتفادي تجمّد السيرفر
    try:
        await asyncio.wait_for(queue_service.enqueue_job(job_data), timeout=1.0)
    except asyncio.TimeoutError:
        print("[Queue Warning] Redis connection timed out. Skipping queue, worker will read from disk.")
    except Exception as e:
        print(f"[Queue Warning] Redis queue error: {e}")

    # إرجاع الرد الفوري للواجهة
    return {
        "success": True,
        "job_id": job.job_id,
        "data": {"job_id": job.job_id},
        "status": job.status.value,
        "operation": job.operation,
        "files": input_files_metadata
    }