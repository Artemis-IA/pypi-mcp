"""TaskManager for async workflows (SEP-1686)."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import Task, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages async tasks for long-running operations."""

    _tasks: dict[str, Task] = {}
    _results: dict[str, TaskResult] = {}
    _statuses: dict[str, TaskStatus] = {}

    @classmethod
    def create_task(cls, task_type: str, payload: dict[str, Any], estimated_duration: str = "medium") -> Task:
        """Create a new async task."""
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        task = Task(
            task_id=task_id,
            type=task_type,
            status="pending",
            estimated_duration=estimated_duration,
            message="Task created",
            created_at=now,
        )
        cls._tasks[task_id] = task
        cls._statuses[task_id] = TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0.0,
            message="Task created",
            created_at=now,
            updated_at=now,
        )
        logger.info(f"Task {task_id} created (type={task_type})")
        return task

    @classmethod
    def update_status(
        cls,
        task_id: str,
        status: str,
        progress: float | None = None,
        message: str = "",
    ) -> TaskStatus:
        """Update the status of a task."""
        if task_id not in cls._statuses:
            raise ValueError(f"Task {task_id} not found")
        ts = cls._statuses[task_id]
        ts.status = status
        if progress is not None:
            ts.progress = progress
        if message:
            ts.message = message
        ts.updated_at = datetime.now(timezone.utc).isoformat()
        if status in ("completed", "failed", "cancelled"):
            ts.completed_at = ts.updated_at
            if task_id in cls._tasks:
                cls._tasks[task_id].status = status
        logger.info(f"Task {task_id} status={status} progress={ts.progress}")
        return ts

    @classmethod
    def store_result(cls, task_id: str, result: dict[str, Any], error: str | None = None) -> TaskResult:
        """Store the result of a completed task."""
        now = datetime.now(timezone.utc).isoformat()
        task_result = TaskResult(
            task_id=task_id,
            status=cls._statuses.get(task_id, TaskStatus(task_id=task_id, status="unknown")).status,
            result=result,
            error=error,
            completed_at=now,
        )
        cls._results[task_id] = task_result
        return task_result

    @classmethod
    def get_status(cls, task_id: str) -> TaskStatus:
        """Get the current status of a task."""
        if task_id not in cls._statuses:
            raise ValueError(f"Task {task_id} not found")
        return cls._statuses[task_id]

    @classmethod
    def get_result(cls, task_id: str) -> TaskResult:
        """Get the result of a completed task."""
        if task_id not in cls._results:
            raise ValueError(f"Result for task {task_id} not found")
        return cls._results[task_id]

    @classmethod
    def list_tasks(cls) -> list[TaskStatus]:
        """List all known task statuses."""
        return list(cls._statuses.values())
