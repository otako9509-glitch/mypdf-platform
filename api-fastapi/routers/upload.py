import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from config import settings
from services.job_service import job_service, JobStatus
from processors.merge import merge_pdfs
from processors.compress import compress_pdf
from processors.rotate import rotate_pdf
from processors.split import split_all_pages
from processors.jpg_to_pdf import jpg_to_pdf
from processors.protect import protect_pdf, unlock_pdf

router = APIRouter()

def execute_pdf_job(job_id: str, operation: str, input_paths: List[str], extra_params: dict = None):
    """
    تنفيذ المعالجة في الخلفية فوراً دون الحاجة إلى خادم Redis أو Worker منفصل
    """
    extra_params = extra_params or {}
    job_service.update_job_status(job_id, JobStatus.PROCESSING)
    
    output_filename = f"{job_id}_output.pdf"
    output_path = os.path.join(settings.OUTPUTS_PATH, output_filename)

    try:
        if operation == "merge":
            if len(input_paths) < 2:
                raise ValueError("دمج PDF يحتاج لملفين على الأقل")
            merge_pdfs(input_paths, output_path)

        elif operation == "compress":
            compress_pdf(input_paths[0], output_path, quality="medium")

        elif operation == "rotate":
            rotation = int(extra_params.get("rotation", 90))
            rotate_pdf(input_paths[0], output_path, rotation=rotation)

        elif operation == "split":
            split_dir = os.path.join(settings.OUTPUTS_PATH, f"{job_id}_split")
            split_files = split_all_pages(input_paths[0], split_dir)
            if split_files:
                output_path = split_files[0]
                output_filename = os.path.basename(output_path)
            else:
                raise ValueError("فشلت عملية التقسيم")

        elif operation in ["jpg-to-pdf", "jpg_to_pdf"]:
            jpg_to_pdf(input_paths, output_path)

        elif operation == "protect":
            password = extra_params.get("password", "123456")
            protect_pdf(input_paths[0], output_path, password=password)

        elif operation == "unlock":
            password = extra_params.get("password", "")
            unlock_pdf(input_paths[0], output_path, password=password)

        else:
            raise ValueError(f"العملية غير مدعومة: {operation}")

        # تحديث الحالة إلى COMPLETED مع تسجيل اسم ملف التحميل
        job_service.update_job_status(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            output_file=output_filename
        )

    except Exception as e:
        job_service.update_job_status(
            job_id=job_id,
            status=JobStatus.FAILED,
            error=str(e)
        )

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    operation: str = Form(...),
    files: List[UploadFile] = File(...),
    password: str = Form(None),
    rotation: int = Form(90)
):
    if not files:
        raise HTTPException(status_code=400, detail="المرجو اختيار ملف")

    # التأكد من وجود مجلدات التخزين
    os.makedirs(settings.UPLOADS_PATH, exist_ok=True)
    os.makedirs(settings.OUTPUTS_PATH, exist_ok=True)
    os.makedirs(settings.JOBS_PATH, exist_ok=True)

    job_id = str(uuid.uuid4())
    saved_paths = []
    input_metadata = []

    # حفظ الملفات المرفوعة مؤقتاً
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        unique_name = f"{job_id}_{uuid.uuid4().hex[:8]}{ext}"
        destination = os.path.join(settings.UPLOADS_PATH, unique_name)

        content = await file.read()
        with open(destination, "wb") as buffer:
            buffer.write(content)

        saved_paths.append(destination)
        input_metadata.append({
            "original_name": file.filename,
            "stored_name": unique_name
        })

    # تسجيل المهمة بحالة PENDING
    job = job_service.create_job(operation=operation, input_files=input_metadata)
    job.job_id = job_id
    job_service._save_job(job)

    extra_params = {
        "password": password,
        "rotation": rotation
    }

    # إضافة المعالجة إلى قائمة مهام الخلفية الفورية
    background_tasks.add_task(execute_pdf_job, job_id, operation, saved_paths, extra_params)

    return {
        "success": True,
        "job_id": job_id,
        "status": "PENDING",
        "operation": operation
    }
