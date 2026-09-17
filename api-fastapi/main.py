import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="MyPDF API",
    description="PDF processing API for MyPDF",
    version="1.0.0"
)

# السماح لجميع النطاقات (CORS) لحل مشكلة الاتصال من Vercel نهائياً
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مسارات التخزين المؤقت
BASE_DIR = "/tmp/mypdf"
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# قاعدة بيانات مؤقتة لتتبع المهام في الذاكرة
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

def process_pdf_task(job_id: str, operation: str, file_paths: List[str]):
    try:
        job_dir = os.path.join(OUTPUTS_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        output_filename = f"result_{operation}.pdf"
        output_file_path = os.path.join(job_dir, output_filename)

        # محاكاة العملية بنسخ الملف الأول كمخرج للتجربة
        if file_paths:
            shutil.copyfile(file_paths[0], output_file_path)

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
            "error": str(e)
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
        raise HTTPException(status_code=400, detail="No files provided")

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

    background_tasks.add_task(process_pdf_task, job_id, operation, saved_files)

    return {
        "success": True,
        "job_id": job_id,
        "message": "File received and processing started"
    }

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": job}

@app.get("/api/v1/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = os.path.join(OUTPUTS_DIR, job_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
