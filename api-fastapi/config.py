import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings

# تحديد المسار الجذري تلقائياً (يمشي في Windows و Linux)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # API Settings
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "MyPDF API"
    API_VERSION: str = "1.0.0"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8080))

    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Storage Paths (مسارات ديناميكية وموحدة)
    STORAGE_PATH: Path = PROJECT_ROOT / "storage"
    UPLOADS_PATH: Path = STORAGE_PATH / "uploads"
    OUTPUTS_PATH: Path = STORAGE_PATH / "outputs"
    JOBS_PATH: Path = STORAGE_PATH / "jobs"

    # Database Settings
    DATABASE_URL: str = f"sqlite+aiosqlite:///{PROJECT_ROOT}/database/app.db"

    # Redis Queue Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    QUEUE_NAME: str = "pdf_jobs"

    # Governance
    JOB_EXPIRATION_HOURS: int = 2
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_FILES_PER_JOB: int = 20

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# التأكد من إنشاء المجلدات فوراً
for p in [settings.STORAGE_PATH, settings.UPLOADS_PATH, settings.OUTPUTS_PATH, settings.JOBS_PATH]:
    p.mkdir(parents=True, exist_ok=True)
