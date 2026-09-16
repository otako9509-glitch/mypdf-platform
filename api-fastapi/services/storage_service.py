import re
from pathlib import Path
from config import settings

OPERATION_MAP = {
    "merge": "merge",
    "split": "split",
    "compress": "compress",
    "rotate": "rotate",
    "organize": "organize",
    "watermark": "watermark",
    "protect": "protect",
    "unlock": "unlock",
    "pdf-to-jpg": "pdf_to_jpg",
    "pdf_to_jpg": "pdf_to_jpg",
    "jpg-to-pdf": "jpg_to_pdf",
    "jpg_to_pdf": "jpg_to_pdf"
}


class StorageService:
    @staticmethod
    def normalize_operation(op: str) -> str:
        """توحيد أسماء العمليات بين الفرونت إند والباك إند"""
        cleaned = op.strip().lower()
        if cleaned not in OPERATION_MAP:
            raise ValueError(f"Unsupported operation: {op}")
        return OPERATION_MAP[cleaned]

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """تنظيف اسم الملف وحماية النظام من ثغرات Path Traversal ودعم العربية"""
        clean_name = Path(filename).name
        clean_name = re.sub(r'[^a-zA-Z0-9_.\-\u0600-\u06FF]', '_', clean_name)
        return clean_name or "document.pdf"

    @staticmethod
    def get_job_upload_dir(job_id: str) -> Path:
        """مسار مجلد رفع الملفات الخاص بكل مهمة"""
        path = settings.UPLOADS_PATH / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_job_output_dir(job_id: str) -> Path:
        """مسار مجلد الملفات الناتجة الخاص بكل مهمة"""
        path = settings.OUTPUTS_PATH / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def validate_magic_bytes(content: bytes, is_pdf: bool = True) -> bool:
        """التحقق من صحة الملف الحقيقي عبر الـ Magic Bytes"""
        if is_pdf:
            return content.startswith(b"%PDF-")
        # التحقق من صور JPG و PNG
        return content.startswith(b"\xFF\xD8\xFF") or content.startswith(b"\x89PNG\r\n\x1a\n")


storage_service = StorageService()
