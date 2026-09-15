import redis.asyncio as redis
from typing import Optional, Dict, Any
import json
from config import settings


class QueueService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.queue_name = "pdf_jobs"
    
    async def connect(self):
        """Connect to Redis."""
        self.redis_client = await redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        await self.redis_client.ping()
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def enqueue_job(self, job_data: Dict[str, Any]) -> bool:
        """Add a job to the queue."""
        try:
            await self.redis_client.lpush(self.queue_name, json.dumps(job_data))
            return True
        except Exception as e:
            print(f"Error enqueuing job: {e}")
            return False
    
    async def dequeue_job(self) -> Optional[Dict[str, Any]]:
        """Get a job from the queue (blocking)."""
        try:
            result = await self.redis_client.brpop(self.queue_name, timeout=5)
            if result:
                _, job_data = result
                return json.loads(job_data)
            return None
        except Exception as e:
            print(f"Error dequeuing job: {e}")
            return None
    
    async def get_queue_length(self) -> int:
        """Get the current queue length."""
        try:
            return await self.redis_client.llen(self.queue_name)
        except Exception as e:
            print(f"Error getting queue length: {e}")
            return 0
    
    async def clear_queue(self) -> bool:
        """Clear all jobs from the queue."""
        try:
            await self.redis_client.delete(self.queue_name)
            return True
        except Exception as e:
            print(f"Error clearing queue: {e}")
            return False


# Global singleton instance
queue_service = QueueService()
