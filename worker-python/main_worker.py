import sys
import os
import json
import time
import logging
from pathlib import Path
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# تحديد المسارات الديناميكية وربطها مع الباك إند
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.append(str(PROJECT_ROOT / "api-fastapi"))
sys.path.append(str(CURRENT_DIR))

from models.job import Job, JobStatus
from processors import (
    merge_pdfs, split_all_pages, compress_pdf,
    rotate_pdf, organize_pdf, pdf_to_jpg,
    jpg_to_pdf, add_text_watermark, protect_pdf, unlock_pdf
)

# إعداد السجلات (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PDFWorker")

# إعدادات Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
QUEUE_NAME = "pdf_jobs"

# إعداد اتصال قاعدة البيانات المتزامن الخاص بالـ Worker
SYNC_DB_URL = f"sqlite:///{PROJECT_ROOT}/database/app.db"
sync_engine = create_engine(SYNC_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=sync_engine)


def update_db_job(job_id: str, status: JobStatus, output_file: str = None, error: str = None):
    """تحديث حالة المهمة مباشرة داخل قاعدة البيانات"""
    try:
        with SessionLocal() as session:
            job = session.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = status
                if output_file:
                    job.output_file = output_file
                if error:
                    job.error = error
                session.commit()
    except Exception as e:
        logger.error(f"Failed to update database for job {job_id}: {e}")


def process_job(payload: dict):
    """معالجة المهمة بحسب نوع العملية المستلمة"""
    job_id = payload["job_id"]
    operation = payload["operation"]
    input_files = payload.get("input_files", [])
    options = payload.get("options", {})

    logger.info(f"--- Started Job {job_id} | Operation: {operation} ---")
    update_db_job(job_id, JobStatus.PROCESSING)

    out_dir = PROJECT_ROOT / "storage" / "outputs" / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_filename = f"{job_id}_processed.pdf"
    target_out_path = out_dir / out_filename

    input_paths = [f["path"] for f in input_files if "path" in f and Path(f["path"]).is_file()]
    if not input_paths:
        raise FileNotFoundError("Input files not found on disk.")

    # توجيه المهمة إلى المعالج المخصص
    if operation == "merge":
        merge_pdfs(input_paths, str(target_out_path))
    elif operation == "compress":
        compress_pdf(input_paths[0], str(target_out_path), quality=options.get("compression_level", "medium"))
    elif operation == "rotate":
        rotate_pdf(input_paths[0], str(target_out_path), rotation=int(options.get("rotation", 90)))
    elif operation == "split":
        split_files = split_all_pages(input_paths[0], str(out_dir))
        out_filename = Path(split_files[0]).name
    elif operation == "organize":
        order = json.loads(options["page_order"]) if isinstance(options.get("page_order"), str) else options.get("page_order")
        organize_pdf(input_paths[0], str(target_out_path), page_order=order)
    elif operation == "pdf_to_jpg":
        res = pdf_to_jpg(input_paths[0], str(out_dir))
        out_filename = Path(res).name
    elif operation == "jpg_to_pdf":
        jpg_to_pdf(input_paths, str(target_out_path))
    elif operation == "watermark":
        add_text_watermark(input_paths[0], str(target_out_path), text=options.get("watermark_text", "CONFIDENTIAL"))
    elif operation == "protect":
        protect_pdf(input_paths[0], str(target_out_path), password=options.get("password", "123456"))
    elif operation == "unlock":
        unlock_pdf(input_paths[0], str(target_out_path), password=options.get("password", ""))
    else:
        raise ValueError(f"Unknown operation: {operation}")

    update_db_job(job_id, JobStatus.COMPLETED, output_file=out_filename)
    logger.info(f"--- Completed Job {job_id} successfully ---")


def run_worker():
    """حلقة الاستماع المستمرة لطابور المهام"""
    logger.info("Initializing PDF Worker...")
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    while True:
        try:
            task = client.brpop(QUEUE_NAME, timeout=3)
            if task:
                _, raw_data = task
                payload = json.loads(raw_data)
                try:
                    process_job(payload)
                except Exception as ex:
                    logger.error(f"Job processing error: {ex}")
                    update_db_job(payload.get("job_id"), JobStatus.FAILED, error=str(ex))
        except redis.ConnectionError:
            logger.warning("Redis disconnected. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected worker error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_worker()
