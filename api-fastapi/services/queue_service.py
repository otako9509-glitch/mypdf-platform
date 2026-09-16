import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.queue_name = settings.QUEUE_NAME

    async def connect(self):
        """الاتصال بخادم Redis والتحقق من الاستجابة"""
        try:
            self.redis_client = await redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None

    async def disconnect(self):
        """قطع الاتصال بخادم Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def enqueue_job(self, job_data: Dict[str, Any]) -> bool:
        """إرسال حمولة المهمة المنظمة إلى الطابور"""
        if not self.redis_client:
            await self.connect()

        if not self.redis_client:
            logger.error("Cannot enqueue job: Redis is unavailable.")
            return False

        try:
            payload = json.dumps(job_data, ensure_ascii=False)
            await self.redis_client.lpush(self.queue_name, payload)
            return True
        except Exception as e:
            logger.error(f"Error enqueuing job {job_data.get('job_id')}: {e}")
            return False

    async def get_queue_length(self) -> int:
        """معرفة عدد المهام العالقة في الطابور"""
        if not self.redis_client:
            return 0
        try:
            return await self.redis_client.llen(self.queue_name)
        except Exception:
            return 0


queue_service = QueueService()
