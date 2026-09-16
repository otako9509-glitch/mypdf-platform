import io
import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


def create_text_watermark_layer(text: str, width: float, height: float, opacity: float = 0.3, color: str = "#888888") -> PdfReader:
    """توليد طبقة PDF شفافة تحتوي على النص المائي في الذاكرة"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    
    try:
        fill_color = HexColor(color)
    except Exception:
        fill_color = HexColor("#888888")
        
    can.setFillColor(fill_color, alpha=opacity)
    can.setFont("Helvetica-Bold", 42)
    can.saveState()
    can.translate(width / 2.0, height / 2.0)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    
    packet.seek(0)
    return PdfReader(packet)


def add_text_watermark(input_file: str, output_path: str, text: str = "CONFIDENTIAL", opacity: float = 0.3, position: str = "center", rotation: int = 45, color: str = "#888888") -> bool:
    """دمج النص المائي فوق كل صفحة من صفحات المستند"""
    in_p = Path(input_file)
    out_p = Path(output_path)

    if not in_p.is_file():
        raise FileNotFoundError(f"الملف غير موجود: {input_file}")

    out_p.parent.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(in_p))
    writer = PdfWriter()

    for page in reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        watermark_layer = create_text_watermark_layer(text, w, h, opacity=opacity, color=color)
        page.merge_page(watermark_layer.pages[0])
        writer.add_page(page)

    with open(out_p, "wb") as f:
        writer.write(f)

    return True


def add_image_watermark(input_file: str, output_path: str, image_path: str, opacity: float = 0.5, position: str = "center") -> bool:
    """دالة احتياطية للعلامة المائية بالصور"""
    return add_text_watermark(input_file, output_path, text="WATERMARK", opacity=opacity)
