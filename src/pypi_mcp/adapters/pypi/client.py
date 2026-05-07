"""PyPI adapter implementing the AbstractRegistryClient interface."""

from typing import Any

from pypi_mcp.core import PyPIClient
from pypi_mcp.core.registry import AbstractRegistryClient


class PyPIAdapter(AbstractRegistryClient):
    """Adapter for PyPI registry."""

    ecosystem: str = "pypi"

    def __init__(self) -> None:
        self._client = PyPIClient()

    async def get_package_info(self, package_name: str) -> dict[str, Any]:
        return await self._client.get_package_info(package_name)

    async def get_latest_version(self, package_name: str) -> str:
        return await self._client.get_latest_version(package_name)

    async def get_versions(self, package_name: str) -> list[str]:
        return await self._client.get_package_versions(package_name)

    async def search_packages(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return await self._client.search_packages(query, limit=limit)

    async def get_download_stats(self, package_name: str, period: str = "month") -> dict[str, Any]:
        return await self._client.get_download_stats(package_name, period)

    async def close(self) -> None:
        await self._client.close()
