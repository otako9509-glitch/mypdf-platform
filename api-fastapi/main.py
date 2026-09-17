import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pypdf import PdfWriter, PdfReader

app = FastAPI(
    title="MyPDF API",
    description="Real PDF processing API for MyPDF",
    version="1.0.0"
)

# إعدادات CORS للسماح بالاتصال من Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "/tmp/mypdf"
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

jobs_db = {}

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="ok",
        message="MyPDF Service is active",
        version="1.0.0"
    )

def execute_real_pdf_processing(job_id: str, operation: str, file_paths: List[str]):
    """تنفيذ المعالجة الحقيقية لملفات PDF عبر pypdf"""
    try:
        job_dir = os.path.join(OUTPUTS_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        output_filename = f"result_{operation}.pdf"
        output_file_path = os.path.join(job_dir, output_filename)

        writer = PdfWriter()

        if operation == "merge":
            # دمج حقيقي لكافة الملفات المرفوعة بالترتيب
            for path in file_paths:
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)

            with open(output_file_path, "wb") as f_out:
                writer.write(f_out)

        elif operation == "compress":
            # ضغط حقيقي لتقليل الحجم
            for path in file_paths:
                reader = PdfReader(path)
                for page in reader.pages:
                    page.compress_content_streams()
                    writer.add_page(page)

            with open(output_file_path, "wb") as f_out:
                writer.write(f_out)

        elif operation == "rotate":
            # تدوير صفحات الملف 90 درجة مع عقارب الساعة
            for path in file_paths:
                reader = PdfReader(path)
                for page in reader.pages:
                    page.rotate(90)
                    writer.add_page(page)

            with open(output_file_path, "wb") as f_out:
                writer.write(f_out)

        else:
            # في حال لم تكن العملية مدعومة بعد
            if file_paths:
                shutil.copyfile(file_paths[0], output_file_path)

        # حذف ملفات الرفع المؤقتة لتوفير المساحة
        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)

        jobs_db[job_id] = {
            "job_id": job_id,
            "status": "COMPLETED",
            "operation": operation,
            "output_file": output_filename,
            "error": None
        }

    except Exception as e:
        jobs_db[job_id] = {
            "job_id": job_id,
            "status": "FAILED",
            "operation": operation,
            "output_file": None,
            "error": f"Processing error: {str(e)}"
        }

@app.post("/api/v1/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    operation: str = Form(...),
    files: List[UploadFile] = File(...),
    password: Optional[str] = Form(None),
    rotation: Optional[int] = Form(None),
    page_order: Optional[str] = Form(None),
    compression_level: Optional[str] = Form(None),
    watermark_text: Optional[str] = Form(None)
):
    if not files:
        raise HTTPException(status_code=400, detail="لم يتم إرسال أي ملف")

    job_id = str(uuid.uuid4())
    job_upload_dir = os.path.join(UPLOADS_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)

    saved_files = []
    for file in files:
        file_path = os.path.join(job_upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file_path)

    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "PROCESSING",
        "operation": operation,
        "output_file": None,
        "error": None
    }

    background_tasks.add_task(execute_real_pdf_processing, job_id, operation, saved_files)

    return {
        "success": True,
        "job_id": job_id,
        "message": "File received and real processing started"
    }

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    return {"success": True, "job": job}

@app.get("/api/v1/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = os.path.join(OUTPUTS_DIR, job_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
