"""
Task Queue Service — A lightweight in-memory task queue with priority scheduling.
Supports adding tasks with priority, processing in order, and status tracking.
"""
import heapq
import time
import uuid
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(order=True)
class Task:
    priority: int
    created_at: float = field(compare=False, default_factory=time.time)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    name: str = field(compare=False, default="unnamed")
    payload: dict = field(compare=False, default_factory=dict)
    status: TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    result: Optional[str] = field(compare=False, default=None)


class TaskQueue:
    """Priority-based task queue with O(log n) insert and O(log n) pop."""

    def __init__(self, max_size: int = 1000):
        self._heap: list[Task] = []
        self._index: dict[str, Task] = {}
        self._max_size = max_size
        self._processed_count = 0

    def add_task(self, name: str, payload: dict, priority: int = 5) -> Task:
        if len(self._heap) >= self._max_size:
            raise OverflowError(f"Queue is full (max {self._max_size} tasks)")
        task = Task(priority=priority, name=name, payload=payload)
        heapq.heappush(self._heap, task)
        self._index[task.task_id] = task
        return task

    def process_next(self) -> Optional[Task]:
        while self._heap:
            task = heapq.heappop(self._heap)
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.PROCESSING
                try:
                    task.result = self._execute(task)
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.result = str(e)
                    task.status = TaskStatus.FAILED
                self._processed_count += 1
                return task
        return None

    def _execute(self, task: Task) -> str:
        return json.dumps({"executed": task.name, "payload": task.payload})

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        task = self._index.get(task_id)
        return task.status if task else None

    @property
    def pending_count(self) -> int:
        return sum(1 for t in self._heap if t.status == TaskStatus.PENDING)

    @property
    def stats(self) -> dict:
        return {
            "queue_size": len(self._heap),
            "pending": self.pending_count,
            "processed": self._processed_count,
            "max_size": self._max_size,
        }


def main():
    queue = TaskQueue(max_size=100)
    # Add tasks with different priorities (lower number = higher priority)
    t1 = queue.add_task("Send email", {"to": "user@example.com"}, priority=3)
    t2 = queue.add_task("Generate report", {"format": "pdf"}, priority=1)
    t3 = queue.add_task("Sync database", {"table": "users"}, priority=2)
    t4 = queue.add_task("Clean cache", {"ttl_hours": 24}, priority=5)

    print("Task Queue Service — Demo")
    print(f"Queue stats: {json.dumps(queue.stats, indent=2)}")

    while True:
        task = queue.process_next()
        if not task:
            break
        print(f"  Processed: {task.name} (priority={task.priority}) => {task.status.value}")

    print(f"\nFinal stats: {json.dumps(queue.stats, indent=2)}")
    print(f"Task {t1.task_id[:8]} status: {queue.get_status(t1.task_id).value}")


if __name__ == "__main__":
    main()
