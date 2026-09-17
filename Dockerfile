# استخدام بيئة بايثون خفيفة ومستقرة
FROM python:3.11-slim

# ضبط متغيرات البيئة لمنع ملفات بايثون المؤقتة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# تثبيت الحزم والأدوات الأساسية للنظام للتعامل مع ملفات PDF والصور
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# نسخ وتثبيت متطلبات المشروع
COPY api-fastapi/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع إلى الحاوية
COPY api-fastapi/ .

# تحديد المنفذ الافتراضي
ENV PORT=8080
EXPOSE 8080

# أمر تشغيل السيرفر تلقائياً مع المنفذ المحدد من Render
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
