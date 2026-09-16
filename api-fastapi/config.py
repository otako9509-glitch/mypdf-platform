import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# تحديد المسار الجذري للمشروع بشكل ديناميكي (يعمل على Windows و Linux/Render)
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # API Settings
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "MyPDF API"
    API_VERSION: str = "1.0.0"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8080))

    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Storage Paths (مسارات نسبية ديناميكية داخل بيئة السيرفر)
    STORAGE_PATH: str = str(BASE_DIR / "storage")
    UPLOADS_PATH: str = str(BASE_DIR / "storage" / "uploads")
    OUTPUTS_PATH: str = str(BASE_DIR / "storage" / "outputs")
    JOBS_PATH: str = str(BASE_DIR / "storage" / "jobs")

    # Job Settings
    JOB_EXPIRATION_HOURS: int = 2
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
