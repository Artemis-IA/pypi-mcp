"""npm adapter implementing the AbstractRegistryClient interface (placeholder)."""

from typing import Any

from pypi_mcp.core.registry import AbstractRegistryClient


class NPMAdapter(AbstractRegistryClient):
    """Adapter for npm registry (placeholder — not yet implemented)."""

    ecosystem: str = "npm"

    async def get_package_info(self, package_name: str) -> dict[str, Any]:
        raise NotImplementedError("npm adapter not yet implemented")

    async def get_latest_version(self, package_name: str) -> str:
        raise NotImplementedError("npm adapter not yet implemented")

    async def get_versions(self, package_name: str) -> list[str]:
        raise NotImplementedError("npm adapter not yet implemented")

    async def search_packages(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        raise NotImplementedError("npm adapter not yet implemented")

    async def get_download_stats(self, package_name: str, period: str = "month") -> dict[str, Any]:
        raise NotImplementedError("npm adapter not yet implemented")

    async def close(self) -> None:
        pass
