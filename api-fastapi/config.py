import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings

# تحديد المسار الجذري للمشروع بشكل ديناميكي
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # إعدادات الـ API
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "MyPDF API"
    API_VERSION: str = "1.0.0"

    # إعدادات السيرفر
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # إعدادات CORS
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # إعدادات Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # مسار قاعدة البيانات الآمن
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/database/app.db"

    # مسارات التخزين
    STORAGE_PATH: str = str(BASE_DIR / "storage")
    UPLOADS_PATH: str = str(BASE_DIR / "storage" / "uploads")
    OUTPUTS_PATH: str = str(BASE_DIR / "storage" / "outputs")
    JOBS_PATH: str = str(BASE_DIR / "storage" / "jobs")

    # صلاحية الملفات
    JOB_EXPIRATION_HOURS: int = 2
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB

    # إعدادات الحماية
    SECRET_KEY: str = "mypdf-secure-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()