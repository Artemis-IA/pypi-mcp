"""Abstract registry client for multi-ecosystem package discovery."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractRegistryClient(ABC):
    """Abstract client for any package registry (PyPI, npm, Maven, etc.)."""

    ecosystem: str = ""

    @abstractmethod
    async def get_package_info(self, package_name: str) -> dict[str, Any]:
        """Fetch package metadata from the registry."""

    @abstractmethod
    async def get_latest_version(self, package_name: str) -> str:
        """Fetch the latest version of a package."""

    @abstractmethod
    async def get_versions(self, package_name: str) -> list[str]:
        """Fetch all available versions of a package."""

    @abstractmethod
    async def search_packages(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for packages matching a query."""

    @abstractmethod
    async def get_download_stats(self, package_name: str, period: str = "month") -> dict[str, Any]:
        """Fetch download statistics for a package."""

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections."""
