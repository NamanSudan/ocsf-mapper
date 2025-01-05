from typing import Dict, Any, Optional
import json
import logging
import redis
from datetime import datetime

logger = logging.getLogger(__name__)

class QueueHandler:
    """
    Handles message queue operations using Redis
    """
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.log_queue = "logs_queue"  # Queue for normalized logs

    async def enqueue_log(self, log_data: Dict[str, Any]) -> bool:
        """Enqueue a normalized log for processing"""
        try:
            log_with_metadata = {
                **log_data,
                "queued_at": datetime.utcnow().isoformat()
            }
            self.redis_client.lpush(
                self.log_queue,
                json.dumps(log_with_metadata)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue log: {str(e)}")
            return False

    async def dequeue_log(self, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Dequeue a log for processing"""
        try:
            # Use BRPOP for blocking read with timeout
            result = self.redis_client.brpop(self.log_queue, timeout=timeout)
            if result:
                _, log_data = result
                return json.loads(log_data)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue log: {str(e)}")
            return None

    async def get_queue_length(self) -> int:
        """Get current queue length"""
        try:
            return self.redis_client.llen(self.log_queue)
        except Exception as e:
            logger.error(f"Failed to get queue length: {str(e)}")
            return 0 