"""Action tools for depcheck-mcp — read-write operations on manifests."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import AbstractRegistryClient, PyPIClient, TaskManager
from pypi_mcp.core.models import Task

logger = logging.getLogger(__name__)


def _get_registry_client(ecosystem: str) -> AbstractRegistryClient:
    """Get the appropriate registry client for an ecosystem."""
    if ecosystem == "pypi":
        return PyPIClient()
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")


async def audit_project(path: str, ecosystem: str = "auto") -> Task:
    """Launch an async audit of a project directory.

    Args:
        path: Path to the project directory.
        ecosystem: Package ecosystem ('auto', 'pypi', 'npm').

    Returns:
        Task object to poll for results (SEP-1686).
    """
    # Auto-detect ecosystem
    detected = ecosystem
    if ecosystem == "auto":
        import os
        if os.path.exists(os.path.join(path, "requirements.txt")) or os.path.exists(os.path.join(path, "pyproject.toml")):
            detected = "pypi"
        elif os.path.exists(os.path.join(path, "package.json")):
            detected = "npm"
        else:
            detected = "pypi"

    task = TaskManager.create_task(
        task_type="audit",
        payload={"path": path, "ecosystem": detected},
        estimated_duration="medium",
    )
    logger.info(f"Audit task {task.task_id} created for {path} ({detected})")
    return task


async def get_task_status(task_id: str) -> dict[str, Any]:
    """Get the status of an async task.

    Args:
        task_id: The task ID returned by audit_project.

    Returns:
        Dictionary with task status.
    """
    try:
        status = TaskManager.get_status(task_id)
        return {"task": status.model_dump()}
    except ValueError as e:
        return {"error": str(e)}


async def get_task_result(task_id: str) -> dict[str, Any]:
    """Get the result of a completed async task.

    Args:
        task_id: The task ID returned by audit_project.

    Returns:
        Dictionary with task result.
    """
    try:
        result = TaskManager.get_result(task_id)
        return {"result": result.model_dump()}
    except ValueError as e:
        return {"error": str(e)}


def register(mcp: FastMCP) -> None:
    """Register action tools."""
    mcp.tool()(audit_project)
    mcp.tool()(get_task_status)
    mcp.tool()(get_task_result)
