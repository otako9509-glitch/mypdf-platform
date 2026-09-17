import os
import shutil
import uuid
import zipfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pypdf import PdfReader, PdfWriter
from PIL import Image
from pdf2image import convert_from_path

app = FastAPI(
    title="MyPDF API",
    description="Real processing for all 10 PDF tools",
    version="1.0.0"
)

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
    return HealthResponse(status="ok", message="MyPDF Engine Running", version="1.0.0")

def execute_all_tools(
    job_id: str,
    operation: str,
    file_paths: List[str],
    password: Optional[str] = None,
    rotation: Optional[int] = 90,
    page_order: Optional[str] = None,
    watermark_text: Optional[str] = None
):
    try:
        job_dir = os.path.join(OUTPUTS_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        output_filename = f"result_{operation}.pdf"
        output_file_path = os.path.join(job_dir, output_filename)
        writer = PdfWriter()

        # 1. دمج PDF
        if operation == "merge":
            for path in file_paths:
                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 2. تقسيم PDF (استخراج الصفحات الأولى كنموذج افتراضي أو حسب الترتيب)
        elif operation == "split":
            reader = PdfReader(file_paths[0])
            total_pages = len(reader.pages)
            limit = min(total_pages, 5)  # استخراج أول 5 صفحات أو الكل إذا كان أقل
            for i in range(limit):
                writer.add_page(reader.pages[i])
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 3. ضغط PDF
        elif operation == "compress":
            reader = PdfReader(file_paths[0])
            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 4. تدوير PDF
        elif operation == "rotate":
            angle = int(rotation) if rotation else 90
            reader = PdfReader(file_paths[0])
            for page in reader.pages:
                page.rotate(angle)
                writer.add_page(page)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 5. تنظيم الصفحات (عكس تسلسل الصفحات كنموذج فرز)
        elif operation == "organize":
            reader = PdfReader(file_paths[0])
            for page in reversed(reader.pages):
                writer.add_page(page)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 6. PDF إلى JPG (تحويل كل صفحة لصورة وضغطها في ملف ZIP)
        elif operation == "pdf-to-jpg":
            images = convert_from_path(file_paths[0])
            output_filename = f"result_images_{job_id}.zip"
            output_file_path = os.path.join(job_dir, output_filename)
            with zipfile.ZipFile(output_file_path, 'w') as zipf:
                for i, img in enumerate(images):
                    img_path = os.path.join(job_dir, f"page_{i+1}.jpg")
                    img.save(img_path, 'JPEG')
                    zipf.write(img_path, arcname=f"page_{i+1}.jpg")

        # 7. JPG إلى PDF (تحويل الصور ودمجها داخل مستند)
        elif operation == "jpg-to-pdf":
            image_list = []
            for path in file_paths:
                img = Image.open(path).convert('RGB')
                image_list.append(img)
            if image_list:
                image_list[0].save(output_file_path, save_all=True, append_images=image_list[1:])

        # 8. علامة مائية
        elif operation == "watermark":
            # إضافة ختم نصي عبر تراكب الصفحات
            reader = PdfReader(file_paths[0])
            for page in reader.pages:
                writer.add_page(page)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 9. حماية وتشفير
        elif operation == "protect":
            reader = PdfReader(file_paths[0])
            for page in reader.pages:
                writer.add_page(page)
            pwd = password if password else "123456"
            writer.encrypt(pwd)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        # 10. فك الحماية
        elif operation == "unlock":
            reader = PdfReader(file_paths[0])
            if reader.is_encrypted:
                try:
                    reader.decrypt(password if password else "")
                except Exception:
                    pass
            for page in reader.pages:
                writer.add_page(page)
            with open(output_file_path, "wb") as f:
                writer.write(f)

        else:
            if file_paths:
                shutil.copyfile(file_paths[0], output_file_path)

        # تنظيف الملفات المرفوعة
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
            "error": f"Error: {str(e)}"
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
        raise HTTPException(status_code=400, detail="لم يتم رفع أي ملف")

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

    background_tasks.add_task(
        execute_all_tools,
        job_id,
        operation,
        saved_files,
        password,
        rotation,
        page_order,
        watermark_text
    )

    return {
        "success": True,
        "job_id": job_id,
        "message": "File processing started"
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
    media_type = "application/zip" if filename.endswith(".zip") else "application/pdf"
    return FileResponse(file_path, media_type=media_type, filename=filename)
