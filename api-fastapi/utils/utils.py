import os
import re
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# تحديد المجلدات الأساسية للتخزين المؤقت
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"
JOBS_DIR = STORAGE_DIR / "jobs"

# الامتدادات المدعومة في المنصة
ALLOWED_EXTENSIONS = {
    "merge": {".pdf"},
    "split": {".pdf"},
    "compress": {".pdf"},
    "rotate": {".pdf"},
    "organize": {".pdf"},
    "pdf-to-jpg": {".pdf"},
    "jpg-to-pdf": {".jpg", ".jpeg", ".png"},
    "watermark": {".pdf"},
    "protect": {".pdf"},
    "unlock": {".pdf"},
}


def ensure_storage_dirs() -> None:
    """التأكد من وجود مجلدات التخزين الأساسية عند إقلاع الخادم."""
    for directory in [UPLOAD_DIR, OUTPUT_DIR, JOBS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def generate_job_id() -> str:
    """توليد معرف فريد غير قابل للتكرار لكل عملية معالجة."""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """
    تنظيف اسم الملف من أي مسارات خبيثة أو رموز غير آمنة (Path Traversal Protection).
    """
    # استخراج الاسم الأساسي بدون المسار
    clean_name = os.path.basename(filename)
    # استبدال الرموز غير الآمنة بـ _
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
    return clean_name or f"document_{uuid.uuid4().hex[:8]}.pdf"


def validate_file_extension(filename: str, operation: str) -> bool:
    """التحقق من أن امتداد الملف متوافق مع نوع العملية المطلوبة."""
    ext = Path(filename).suffix.lower()
    allowed = ALLOWED_EXTENSIONS.get(operation, {".pdf"})
    return ext in allowed


def get_job_upload_path(job_id: str, filename: str) -> Path:
    """تحديد مسار حفظ الملف المرفوع داخل مجلد خاص بكل مهمة."""
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir / sanitize_filename(filename)


def get_job_output_path(job_id: str, filename: str) -> Path:
    """تحديد مسار حفظ الملف الناتج بعد إتمام المعالجة."""
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir / sanitize_filename(filename)


def format_file_size(size_in_bytes: int) -> str:
    """تحويل حجم الملف من Bytes إلى صيغة قابلة للقراءة (KB, MB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"


def cleanup_expired_files(max_age_hours: int = 2) -> int:
    """
    حذف تلقائي لكافة الملفات والمجلدات التي تجاوز عمرها ساعتين
    لضمان الحفاظ على الخصوصية وتوفير مساحة التخزين.
    """
    now = datetime.now()
    expiration_limit = now - timedelta(hours=max_age_hours)
    deleted_count = 0

    for target_dir in [UPLOAD_DIR, OUTPUT_DIR, JOBS_DIR]:
        if not target_dir.exists():
            continue

        for item in target_dir.iterdir():
            try:
                item_stat = item.stat()
                mtime = datetime.fromtimestamp(item_stat.st_mtime)

                if mtime < expiration_limit:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                    deleted_count += 1
            except Exception:
                # تجاهل الأخطاء أثناء انشغال الملف بعملية أخرى
                continue

    return deleted_count