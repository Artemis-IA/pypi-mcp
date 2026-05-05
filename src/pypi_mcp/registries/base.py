"""Base registry client for multi-registry extensibility."""

from abc import ABC, abstractmethod
from typing import Any


class BaseRegistryClient(ABC):
    """Abstract base class for package registry clients."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable registry name."""

    @property
    @abstractmethod
    def ecosystem(self) -> str:
        """Ecosystem identifier (e.g., 'PyPI', 'npm', 'Maven')."""

    @abstractmethod
    async def get_package_info(self, package_name: str, version: str | None = None) -> dict[str, Any]:
        """Get package metadata."""

    @abstractmethod
    async def list_versions(self, package_name: str) -> list[str]:
        """List all available versions."""

    @abstractmethod
    async def get_dependencies(self, package_name: str, version: str | None = None) -> dict[str, Any]:
        """Get dependency information."""

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search packages by keyword."""

    @abstractmethod
    async def get_latest_version(self, package_name: str) -> str:
        """Get the latest version."""
