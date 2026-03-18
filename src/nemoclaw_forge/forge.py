import asyncio
import json
import logging
import time
import uuid
import redis.asyncio as redis
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class Forge:
    """Forge Master: Orchestrates workers and tracks status."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.workers: Dict[str, float] = {}  # worker_id -> last_seen_timestamp
        self._running = False
        
    async def connect(self):
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info("Forge connected to Redis.")
        
    async def monitor_heartbeats(self):
        """Subscribe to heartbeat channel."""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("nemoclaw:heartbeat")
        logger.info("Forge monitoring heartbeats...")
        
        while self._running:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message['type'] == 'message':
                data = json.loads(message['data'].decode('utf-8'))
                worker_id = data.get("worker_id")
                if worker_id:
                    self.workers[worker_id] = time.time()
                    
            # Cleanup stale workers (no heartbeat in > 10s)
            now = time.time()
            stale = [w for w, ts in self.workers.items() if now - ts > 10.0]
            for w in stale:
                logger.warning(f"Worker {w} is dead (no heartbeat). Removing from registry.")
                del self.workers[w]
                
    async def dispatch_task(self, worker_id: str, prompt: str) -> str:
        """Dispatch a task to a specific worker and wait for result."""
        task_id = str(uuid.uuid4())
        task_data = json.dumps({"task_id": task_id, "prompt": prompt})
        
        # Subscribe to results channel before publishing
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("nemoclaw:results")
        
        await self.redis_client.publish(f"nemoclaw:tasks:{worker_id}", task_data)
        logger.info(f"Dispatched task {task_id} to {worker_id}")
        
        # Wait for result
        start_time = time.time()
        while time.time() - start_time < 30.0: # 30s timeout
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg['type'] == 'message':
                data = json.loads(msg['data'].decode('utf-8'))
                if data.get("task_id") == task_id:
                    await pubsub.unsubscribe("nemoclaw:results")
                    if data.get("status") == "success":
                        return data.get("result")
                    else:
                        raise RuntimeError(data.get("error"))
        
        await pubsub.unsubscribe("nemoclaw:results")
        raise TimeoutError("Task timed out waiting for result.")

    async def start(self):
        self._running = True
        await self.connect()
        # Start background heartbeat monitor
        asyncio.create_task(self.monitor_heartbeats())
        
    async def stop(self):
        self._running = False
        if self.redis_client:
            await self.redis_client.close()
