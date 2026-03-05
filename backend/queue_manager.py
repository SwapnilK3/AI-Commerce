"""
Queue Manager — Redis task queue with in-memory asyncio.Queue fallback.
Used for async communication task processing.
"""
import asyncio
import json
import logging
from typing import Callable, Awaitable, Optional

logger = logging.getLogger(__name__)

# ── Queue Interface ────────────────────────────────────────


class TaskQueue:
    """Abstract task queue interface."""

    async def enqueue(self, task: dict) -> None:
        raise NotImplementedError

    async def dequeue(self) -> Optional[dict]:
        raise NotImplementedError

    def get_name(self) -> str:
        raise NotImplementedError


# ── Redis Queue ────────────────────────────────────────────


class RedisQueue(TaskQueue):
    """Production queue using Redis."""

    def __init__(self, redis_url: str, queue_name: str = "comm_tasks"):
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(redis_url)
        self._queue_name = queue_name
        logger.info("RedisQueue initialized: %s", redis_url)

    async def enqueue(self, task: dict) -> None:
        await self._redis.rpush(self._queue_name, json.dumps(task))
        logger.info("Task enqueued to Redis: %s", task.get("type", "unknown"))

    async def dequeue(self) -> Optional[dict]:
        data = await self._redis.lpop(self._queue_name)
        if data:
            return json.loads(data)
        return None

    def get_name(self) -> str:
        return "Redis"


# ── In-Memory Queue ────────────────────────────────────────


class InMemoryQueue(TaskQueue):
    """Fallback queue using asyncio.Queue."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        logger.info("InMemoryQueue initialized (fallback)")

    async def enqueue(self, task: dict) -> None:
        await self._queue.put(task)
        logger.info("Task enqueued to memory: %s", task.get("type", "unknown"))

    async def dequeue(self) -> Optional[dict]:
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def get_name(self) -> str:
        return "In-Memory"


# ── Factory ────────────────────────────────────────────────

_queue: Optional[TaskQueue] = None


def create_queue(redis_url: str = "") -> TaskQueue:
    """Create task queue — Redis if available, in-memory fallback."""
    global _queue

    if redis_url and redis_url != "":
        try:
            _queue = RedisQueue(redis_url)
            logger.info("✓ Queue: Using Redis")
            return _queue
        except Exception as e:
            logger.warning("Redis connection failed (%s), falling back to in-memory", str(e))

    _queue = InMemoryQueue()
    logger.info("⟳ Queue: Using In-Memory (fallback)")
    return _queue


def get_queue() -> TaskQueue:
    """Get the active queue instance."""
    global _queue
    if _queue is None:
        _queue = InMemoryQueue()
    return _queue


# ── Background Worker ──────────────────────────────────────

_worker_callback: Optional[Callable[[dict], Awaitable[None]]] = None


def set_worker_callback(callback: Callable[[dict], Awaitable[None]]):
    """Set the function to call when processing dequeued tasks."""
    global _worker_callback
    _worker_callback = callback


async def process_queue_worker():
    """Background worker that continuously processes queued tasks."""
    logger.info("Queue worker started")
    queue = get_queue()

    while True:
        task = await queue.dequeue()
        if task and _worker_callback:
            try:
                await _worker_callback(task)
            except Exception as e:
                logger.error("Queue worker error processing task: %s", str(e))
        else:
            # No tasks, wait briefly
            await asyncio.sleep(0.5)
