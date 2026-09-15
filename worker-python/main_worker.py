import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Optional
import redis

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors import (
    merge_pdfs, split_all_pages, compress_pdf,
    rotate_pdf, organize_pdf,
    pdf_to_jpg, jpg_to_pdf,
    add_text_watermark, add_image_watermark,
    protect_pdf, unlock_pdf
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
JOBS_STORAGE_PATH = "C:\\Users\\ADIL\\Documents\\pj\\storage\\jobs"
UPLOADS_PATH = "C:\\Users\\ADIL\\Documents\\pj\\storage\\uploads"
OUTPUTS_PATH = "C:\\Users\\ADIL\\Documents\\pj\\storage\\outputs"
POLL_INTERVAL = 2  # seconds
QUEUE_NAME = "pdf_jobs"


class JobStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def get_job_file_path(job_id: str) -> str:
    """Get the file path for a job's metadata."""
    return os.path.join(JOBS_STORAGE_PATH, f"{job_id}.json")


def load_job(job_id: str) -> Optional[dict]:
    """Load job metadata from disk."""
    job_file = get_job_file_path(job_id)
    if not os.path.exists(job_file):
        return None
    
    try:
        with open(job_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading job {job_id}: {e}")
        return None


def save_job(job_data: dict) -> bool:
    """Save job metadata to disk."""
    job_file = get_job_file_path(job_data['job_id'])
    try:
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving job {job_data['job_id']}: {e}")
        return False


def update_job_status(job_id: str, status: str, output_file: Optional[str] = None, error: Optional[str] = None) -> bool:
    """Update job status atomically."""
    job_data = load_job(job_id)
    if not job_data:
        return False
    
    job_data['status'] = status
    job_data['updated_at'] = datetime.utcnow().isoformat()
    
    if output_file is not None:
        job_data['output_file'] = output_file
    
    if error is not None:
        job_data['error'] = error
    
    return save_job(job_data)


def get_upload_file_path(stored_name: str) -> Optional[str]:
    """Get the full path of an uploaded file."""
    file_path = os.path.join(UPLOADS_PATH, stored_name)
    if os.path.exists(file_path):
        return file_path
    return None


def process_job(job_data: dict) -> bool:
    """Process a single job based on its operation type."""
    job_id = job_data['job_id']
    operation = job_data['operation']
    input_files = job_data.get('input_files', [])
    
    logger.info(f"Processing job {job_id} with operation: {operation}")
    
    # Update status to PROCESSING
    if not update_job_status(job_id, JobStatus.PROCESSING):
        logger.error(f"Failed to update job {job_id} to PROCESSING")
        return False
    
    try:
        # Build input file paths
        input_paths = []
        for file_info in input_files:
            stored_name = file_info.get('stored_name')
            if stored_name:
                input_path = get_upload_file_path(stored_name)
                if os.path.exists(input_path):
                    input_paths.append(input_path)
                else:
                    raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not input_paths:
            raise ValueError("No valid input files found")
        
        # Determine output path
        output_filename = f"{job_id}_output.pdf"
        output_path = os.path.join(OUTPUTS_PATH, output_filename)
        
        # Process based on operation type
        if operation == "merge":
            if len(input_paths) < 2:
                raise ValueError("Merge operation requires at least 2 input files")
            merge_pdfs(input_paths, output_path)
        
        elif operation == "split":
            # For split, we create multiple output files
            split_output_dir = os.path.join(OUTPUTS_PATH, f"{job_id}_split")
            split_files = split_all_pages(input_paths[0], split_output_dir)
            # Store the first split file as the main output
            if split_files:
                output_path = split_files[0]
            else:
                raise ValueError("Split operation produced no output files")
        
        elif operation == "compress":
            compress_pdf(input_paths[0], output_path, quality="medium")
        
        elif operation == "rotate":
            rotation_angle = job_data.get('rotation_angle', 90)
            rotate_pdf(input_paths[0], output_path, rotation=int(rotation_angle))
        
        elif operation == "organize":
            page_order = job_data.get('page_order', [])
            if page_order:
                page_order = json.loads(page_order) if isinstance(page_order, str) else page_order
                organize_pdf(input_paths[0], output_path, page_order)
            else:
                raise ValueError("Page order not provided for organize operation")
        
        elif operation == "pdf_to_jpg":
            image_quality = job_data.get('image_quality', 'medium')
            image_dpi = int(job_data.get('image_dpi', 150))
            result_path = pdf_to_jpg(input_paths[0], OUTPUTS_PATH, quality=image_quality, dpi=image_dpi)
            # If result is a zip file, use that as output
            if result_path:
                output_path = os.path.basename(result_path)
        
        elif operation == "jpg_to_pdf":
            page_orientation = job_data.get('page_orientation', 'auto')
            page_margin = job_data.get('page_margin', 'small')
            jpg_to_pdf(input_paths, output_path, orientation=page_orientation, margin=page_margin)
        
        elif operation == "watermark":
            watermark_type = job_data.get('watermark_type', 'text')
            watermark_text = job_data.get('watermark_text', 'CONFIDENTIAL')
            watermark_opacity = float(job_data.get('watermark_opacity', 0.5))
            watermark_position = job_data.get('watermark_position', 'center')
            watermark_rotation = int(job_data.get('watermark_rotation', 0))
            watermark_color = job_data.get('watermark_color', '#FF0000')
            
            if watermark_type == 'text':
                add_text_watermark(
                    input_paths[0], output_path, watermark_text,
                    opacity=watermark_opacity, position=watermark_position,
                    rotation=watermark_rotation, color=watermark_color
                )
            else:
                # Image watermark - would need image file from upload
                add_text_watermark(
                    input_paths[0], output_path, watermark_text,
                    opacity=watermark_opacity, position=watermark_position
                )
        
        elif operation == "protect":
            password = job_data.get('password', '')
            encryption_level = job_data.get('encryption_level', 'AES-256')
            allow_print = job_data.get('allow_print', True)
            allow_copy = job_data.get('allow_copy', True)
            allow_modify = job_data.get('allow_modify', True)
            
            protect_pdf(
                input_paths[0], output_path, password,
                encryption_level=encryption_level,
                allow_print=allow_print, allow_copy=allow_copy, allow_modify=allow_modify
            )
        
        elif operation == "unlock":
            password = job_data.get('password', '')
            unlock_pdf(input_paths[0], output_path, password)
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        # Update status to COMPLETED
        output_relative_path = os.path.relpath(output_path, OUTPUTS_PATH)
        if not update_job_status(job_id, JobStatus.COMPLETED, output_file=output_relative_path):
            logger.error(f"Failed to update job {job_id} to COMPLETED")
            return False
        
        logger.info(f"Job {job_id} completed successfully")
        return True
        
    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_message}")
        
        # Update status to FAILED
        update_job_status(job_id, JobStatus.FAILED, error=error_message)
        return False


def main():
    """Main worker loop with Redis queue consumer pattern."""
    logger.info("Starting MyPDF worker...")
    logger.info(f"Jobs storage: {JOBS_STORAGE_PATH}")
    logger.info(f"Uploads path: {UPLOADS_PATH}")
    logger.info(f"Outputs path: {OUTPUTS_PATH}")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"Queue: {QUEUE_NAME}")
    
    # Ensure directories exist
    os.makedirs(JOBS_STORAGE_PATH, exist_ok=True)
    os.makedirs(UPLOADS_PATH, exist_ok=True)
    os.makedirs(OUTPUTS_PATH, exist_ok=True)
    
    # Connect to Redis
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.info("Falling back to file-based job polling")
        redis_client = None
    
    jobs_processed = 0
    
    try:
        while True:
            try:
                job_data = None
                
                if redis_client:
                    # Try to get job from Redis queue
                    result = redis_client.brpop(QUEUE_NAME, timeout=POLL_INTERVAL)
                    if result:
                        _, job_json = result
                        job_data = json.loads(job_json)
                else:
                    # Fallback to file-based polling
                    time.sleep(POLL_INTERVAL)
                    # Check for pending jobs in file system
                    if os.path.exists(JOBS_STORAGE_PATH):
                        for filename in os.listdir(JOBS_STORAGE_PATH):
                            if filename.endswith('.json'):
                                job_file = os.path.join(JOBS_STORAGE_PATH, filename)
                                with open(job_file, 'r', encoding='utf-8') as f:
                                    temp_job = json.load(f)
                                    if temp_job.get('status') == JobStatus.PENDING:
                                        job_data = temp_job
                                        break
                
                if job_data:
                    job_id = job_data['job_id']
                    logger.info(f"Processing job: {job_id}")
                    
                    if process_job(job_data):
                        jobs_processed += 1
                    else:
                        logger.warning(f"Failed to process job: {job_id}")
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(POLL_INTERVAL)
    
    except Exception as e:
        logger.error(f"Fatal error in worker: {e}", exc_info=True)
    
    finally:
        if redis_client:
            redis_client.close()
    
    logger.info(f"Worker shutdown. Total jobs processed: {jobs_processed}")


if __name__ == "__main__":
    main()
