"""Abstract security client for vulnerability scanning."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractSecurityClient(ABC):
    """Abstract client for security vulnerability databases (OSV, GHSA, etc.)."""

    @abstractmethod
    async def query_vulnerabilities(
        self,
        package_name: str,
        version: str = "",
        ecosystem: str = "PyPI",
    ) -> list[dict[str, Any]]:
        """Query vulnerabilities for a package."""

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections."""
