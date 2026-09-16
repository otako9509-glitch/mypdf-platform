import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def compress_pdf(input_file: str, output_path: str, quality: str = "medium") -> bool:
    """
    ضغط ملف PDF عبر ضغط تدفقات البيانات بدون حذف النصوص أو إتلاف المحتوى.
    """
    in_p = Path(input_file)
    out_p = Path(output_path)

    if not in_p.is_file():
        raise FileNotFoundError(f"الملف غير موجود: {input_file}")

    out_p.parent.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(in_p))
    writer = PdfWriter()

    for page in reader.pages:
        # تطبيق الضغط الآمن على تدفقات النصوص والرسوم
        page.compress_content_streams()
        writer.add_page(page)

    # الحفاظ على البيانات الوصفية الآمنة
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    with open(out_p, "wb") as f:
        writer.write(f)

    return True


def optimize_pdf_streams(input_file: str, output_path: str) -> bool:
    """دالة توافقية لتحسين تدفقات المستند"""
    return compress_pdf(input_file, output_path, quality="medium")
