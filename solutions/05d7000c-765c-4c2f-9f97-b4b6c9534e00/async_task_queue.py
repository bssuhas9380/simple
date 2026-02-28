import asyncio
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Coroutine
from uuid import uuid4

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"


class Priority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class Task:
    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = ""
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    priority: int = Priority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    status: str = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None

    def to_json(self) -> str:
        d = asdict(self)
        d["args"] = list(d["args"])
        return json.dumps(d)

    @classmethod
    def from_json(cls, data: str) -> "Task":
        d = json.loads(data)
        d["args"] = tuple(d["args"])
        return cls(**d)


class AsyncTaskQueue:
    """Production-ready async task queue using Redis as broker."""

    def __init__(self, redis_url: str = "redis://localhost:6379", queue_name: str = "tasks"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self._redis: aioredis.Redis | None = None
        self._handlers: dict[str, Callable[..., Coroutine]] = {}
        self._running = False

    async def connect(self):
        self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("Connected to Redis at %s", self.redis_url)

    async def close(self):
        if self._redis:
            await self._redis.close()

    def handler(self, name: str):
        """Decorator to register a task handler."""
        def decorator(func: Callable[..., Coroutine]):
            self._handlers[name] = func
            return func
        return decorator

    async def enqueue(self, name: str, *args, priority: Priority = Priority.NORMAL, **kwargs) -> Task:
        """Add a task to the queue with optional priority."""
        task = Task(name=name, args=args, kwargs=kwargs, priority=priority)
        await self._redis.zadd(
            f"{self.queue_name}:pending",
            {task.to_json(): -task.priority},
        )
        await self._redis.hset(f"{self.queue_name}:status", task.id, TaskStatus.PENDING)
        logger.info("Enqueued task %s [%s] priority=%d", task.id, name, priority)
        return task

    async def _execute_task(self, task: Task) -> Task:
        """Execute a single task with retry logic and dead-letter support."""
        handler = self._handlers.get(task.name)
        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for '{task.name}'"
            return task

        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        await self._redis.hset(f"{self.queue_name}:status", task.id, TaskStatus.RUNNING)

        try:
            task.result = await handler(*task.args, **task.kwargs)
            task.status = TaskStatus.SUCCESS
            task.completed_at = time.time()
            logger.info("Task %s completed successfully", task.id)
        except Exception as exc:
            task.error = str(exc)
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                delay = 2 ** task.retry_count
                logger.warning(
                    "Task %s failed, retry %d/%d in %ds",
                    task.id, task.retry_count, task.max_retries, delay,
                )
                await asyncio.sleep(delay)
                await self._redis.zadd(
                    f"{self.queue_name}:pending",
                    {task.to_json(): -task.priority},
                )
            else:
                task.status = TaskStatus.DEAD
                await self._redis.lpush(f"{self.queue_name}:dead_letter", task.to_json())
                logger.error("Task %s dead after %d retries", task.id, task.max_retries)

        await self._redis.hset(f"{self.queue_name}:status", task.id, task.status)
        return task

    async def worker(self, poll_interval: float = 0.5):
        """Start processing tasks from the queue."""
        logger.info("Worker started for queue: %s", self.queue_name)
        self._running = True
        while self._running:
            result = await self._redis.zpopmin(f"{self.queue_name}:pending", count=1)
            if not result:
                await asyncio.sleep(poll_interval)
                continue
            raw, _score = result[0]
            task = Task.from_json(raw)
            logger.info("Processing task %s [%s]", task.id, task.name)
            await self._execute_task(task)

    async def stop(self):
        """Gracefully stop the worker."""
        self._running = False

    async def get_dead_letters(self, count: int = 10) -> list[Task]:
        """Retrieve tasks from the dead letter queue."""
        items = await self._redis.lrange(f"{self.queue_name}:dead_letter", 0, count - 1)
        return [Task.from_json(i) for i in items]

    async def retry_dead_letter(self, task_id: str) -> bool:
        """Move a dead-lettered task back to the pending queue."""
        items = await self._redis.lrange(f"{self.queue_name}:dead_letter", 0, -1)
        for item in items:
            task = Task.from_json(item)
            if task.id == task_id:
                task.retry_count = 0
                task.status = TaskStatus.PENDING
                task.error = None
                await self._redis.lrem(f"{self.queue_name}:dead_letter", 1, item)
                await self._redis.zadd(
                    f"{self.queue_name}:pending",
                    {task.to_json(): -task.priority},
                )
                return True
        return False

    async def queue_stats(self) -> dict:
        """Get current queue statistics."""
        pending = await self._redis.zcard(f"{self.queue_name}:pending")
        dead = await self._redis.llen(f"{self.queue_name}:dead_letter")
        statuses = await self._redis.hgetall(f"{self.queue_name}:status")
        running = sum(1 for s in statuses.values() if s == TaskStatus.RUNNING)
        return {
            "pending": pending,
            "running": running,
            "dead_letters": dead,
            "total_tracked": len(statuses),
        }


async def main():
    """Demo: enqueue tasks, process them, show stats."""
    queue = AsyncTaskQueue()
    await queue.connect()

    @queue.handler("send_email")
    async def send_email(to: str, subject: str, body: str):
        await asyncio.sleep(0.1)
        logger.info("Email sent to %s: %s", to, subject)
        return {"sent": True, "to": to}

    @queue.handler("process_image")
    async def process_image(url: str, width: int, height: int):
        await asyncio.sleep(0.3)
        return {"resized": True, "url": url, "dims": f"{width}x{height}"}

    t1 = await queue.enqueue("send_email", "u@test.com", "Hi", "Body", priority=Priority.HIGH)
    t2 = await queue.enqueue("process_image", "https://img.example.com/p.jpg", 800, 600)
    print(f"Enqueued: {t1.id}, {t2.id}")
    print(f"Stats: {await queue.queue_stats()}")

    worker = asyncio.create_task(queue.worker())
    await asyncio.sleep(2)
    await queue.stop()
    worker.cancel()

    print(f"Final: {await queue.queue_stats()}")
    await queue.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())