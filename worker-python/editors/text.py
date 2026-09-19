import os
import fitz  # PyMuPDF
import base64
from typing import List, Dict, Any


def apply_pdf_edits(input_file: str, output_path: str, edits: List[Dict[str, Any]]) -> bool:
    """
    تطبيق تعديلات المستخدم: مسح/تغطية + إضافة نصوص + إدراج صور
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        doc = fitz.open(input_file)

        for item in edits:
            page_idx = int(item.get("page", 1)) - 1
            if page_idx < 0 or page_idx >= len(doc):
                continue

            page = doc[page_idx]
            edit_type = item.get("type")
            x = float(item.get("x", 0))
            y = float(item.get("y", 0))

            # 1. التغطية البيضاء (تحديد ومسح)
            if edit_type == "whiteout":
                w = float(item.get("width", 100))
                h = float(item.get("height", 24))
                rect = fitz.Rect(x, y, x + w, y + h)
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # 2. كتابة نص جديد
            elif edit_type == "text":
                text = item.get("text", "")
                font_size = float(item.get("fontSize", 16))
                
                # تحويل اللون من Hex إلى RGB
                color_hex = str(item.get("color", "#000000")).lstrip('#')
                if len(color_hex) == 6:
                    rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                else:
                    rgb = (0, 0, 0)
                
                point = fitz.Point(x, y + font_size)
                page.insert_text(point, text, fontsize=font_size, color=rgb)

            # 3. إدراج صورة
            elif edit_type == "image" and "imageData" in item:
                try:
                    img_data = item["imageData"]
                    if "," in img_data:
                        img_data = img_data.split(",")[1]
                    img_bytes = base64.b64decode(img_data)
                    w = float(item.get("width", 120))
                    rect = fitz.Rect(x, y, x + w, y + (w * 0.75))
                    page.insert_image(rect, stream=img_bytes)
                except Exception as img_err:
                    print(f"Error inserting image: {img_err}")

        # إنشاء مجلد الحفظ في حال عدم وجوده
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        doc.close()
        return True

    except Exception as e:
        print(f"Error applying edits: {e}")
        raise e
