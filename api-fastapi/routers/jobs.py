from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.job_service import job_service

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    الاستعلام عن تفاصيل وحالة المهمة عبر معرّفها job_id مباشرة من قاعدة البيانات.
    """
    job = await job_service.get_job(db, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="المهمة غير موجودة. تأكد من صحة رقم المهمة (job_id)."
        )

    return {
        "success": True,
        "job": job.to_dict()
    }
