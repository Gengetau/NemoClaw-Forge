import asyncio
import json
import logging
import redis.asyncio as redis
from typing import Optional

from .brain import Brain
from .sandbox import Sandbox

logger = logging.getLogger(__name__)

class Claw:
    """Claw Worker: Executes tasks and maintains heartbeat."""
    
    def __init__(self, worker_id: str, redis_url: str = "redis://localhost:6379"):
        self.worker_id = worker_id
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.brain = Brain()
        self.sandbox = Sandbox(timeout_seconds=5.0)
        self._running = False
        
    async def connect(self):
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info(f"Claw {self.worker_id} connected to Redis.")
        
    async def heartbeat_loop(self):
        """Publish heartbeat to Redis Pub/Sub."""
        while self._running:
            try:
                message = json.dumps({"worker_id": self.worker_id, "status": "alive"})
                await self.redis_client.publish("nemoclaw:heartbeat", message)
                await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5.0)
                
    async def process_task(self, prompt: str) -> str:
        """Process a task inside a sandbox using the Brain."""
        return await self.sandbox.run_sandboxed(self.brain.execute, prompt)
        
    async def task_listener(self):
        """Listen for tasks assigned to this worker."""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(f"nemoclaw:tasks:{self.worker_id}")
        logger.info(f"Claw {self.worker_id} listening for tasks...")
        
        while self._running:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message['type'] == 'message':
                data = json.loads(message['data'].decode('utf-8'))
                task_id = data.get("task_id")
                prompt = data.get("prompt")
                
                logger.info(f"Claw {self.worker_id} received task {task_id}")
                try:
                    result = await self.process_task(prompt)
                    # Send result back
                    resp = json.dumps({"task_id": task_id, "result": result, "status": "success"})
                    await self.redis_client.publish("nemoclaw:results", resp)
                except Exception as e:
                    resp = json.dumps({"task_id": task_id, "error": str(e), "status": "failed"})
                    await self.redis_client.publish("nemoclaw:results", resp)
                    
    async def start(self):
        self._running = True
        await self.connect()
        # Run loops concurrently
        await asyncio.gather(
            self.heartbeat_loop(),
            self.task_listener()
        )
        
    async def stop(self):
        self._running = False
        if self.redis_client:
            await self.redis_client.close()
