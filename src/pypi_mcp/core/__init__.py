"""Core modules for depcheck-mcp."""

from .cache import TTLCache
from .config import settings
from .exceptions import (
    CacheError,
    InvalidPackageNameError,
    NetworkError,
    OSVError,
    PackageNotFoundError,
    PyPIError,
    PyPIServerError,
    RateLimitError,
)
from .extensions import ExtensionManager
from .models import (
    DependencyInfo,
    DependencyTree,
    DownloadStats,
    ExtensionCapability,
    PackageHealth,
    PackageInfo,
    SecurityReport,
    Task,
    TaskResult,
    TaskStatus,
    VersionInfo,
    Vulnerability,
)
from .osv_client import OSVClient
from .pypi_client import PyPIClient
from .registry import AbstractRegistryClient
from .resolver import AbstractResolver
from .security import AbstractSecurityClient
from .tasks import TaskManager

__all__ = [
    "AbstractRegistryClient",
    "AbstractSecurityClient",
    "AbstractResolver",
    "ExtensionManager",
    "ExtensionCapability",
    "TaskManager",
    "Task",
    "TaskStatus",
    "TaskResult",
    "PyPIClient",
    "OSVClient",
    "settings",
    "TTLCache",
    "PyPIError",
    "PackageNotFoundError",
    "NetworkError",
    "InvalidPackageNameError",
    "RateLimitError",
    "PyPIServerError",
    "OSVError",
    "CacheError",
    "PackageInfo",
    "VersionInfo",
    "DependencyInfo",
    "DependencyTree",
    "DownloadStats",
    "Vulnerability",
    "SecurityReport",
    "PackageHealth",
]
