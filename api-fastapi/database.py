import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# التأكد من وجود المجلد الحاضن لملف قاعدة البيانات
db_path_str = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
if not db_path_str.startswith(":memory:"):
    Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)

# إنشاء المحرك غير المتزامن (Async Engine)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# مصنع الجلسات (Session Factory)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# الفئة الأساسية للنماذج
Base = declarative_base()


async def get_db() -> AsyncSession:
    """حقن التبعية للحصول على جلسة قاعدة بيانات مع rollback تلقائي عند الخطأ"""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """تهيئة الجداول عند إقلاع التطبيق"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """إغلاق اتصال قاعدة البيانات عند إيقاف التطبيق"""
    await engine.dispose()
