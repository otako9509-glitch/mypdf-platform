import json
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.job import Job, JobStatus


class JobService:
    """خدمة موحدة لإدارة المهام بالاعتماد حصراً على قاعدة البيانات"""

    async def create_job(
        self,
        db: AsyncSession,
        job_id: str,
        operation: str,
        input_files: List[Dict[str, Any]]
    ) -> Job:
        """إنشاء مهمة جديدة وتخزينها في قاعدة البيانات"""
        job = Job(
            job_id=job_id,
            operation=operation,
            input_files=json.dumps(input_files, ensure_ascii=False),
            status=JobStatus.PENDING,
            progress=0
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def get_job(self, db: AsyncSession, job_id: str) -> Optional[Job]:
        """جلب بيانات المهمة عبر معرّفها الموحد job_id"""
        stmt = select(Job).where(Job.job_id == job_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def update_job_status(
        self,
        db: AsyncSession,
        job_id: str,
        status: JobStatus,
        output_file: Optional[str] = None,
        error: Optional[str] = None,
        progress: Optional[int] = None
    ) -> Optional[Job]:
        """تحديث حالة المهمة بشكل غير متزامن داخل قاعدة البيانات"""
        values: Dict[str, Any] = {"status": status}
        if output_file is not None:
            values["output_file"] = output_file
        if error is not None:
            values["error"] = error
        if progress is not None:
            values["progress"] = progress

        stmt = update(Job).where(Job.job_id == job_id).values(**values)
        await db.execute(stmt)
        await db.commit()
        return await self.get_job(db, job_id)


# مثيل وحيد للخدمة (Singleton)
job_service = JobService()
