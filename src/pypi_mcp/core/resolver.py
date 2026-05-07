"""Abstract dependency resolver for any ecosystem."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractResolver(ABC):
    """Abstract dependency resolver for any package ecosystem."""

    ecosystem: str = ""

    @abstractmethod
    async def resolve(
        self,
        package_name: str,
        version: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Resolve dependencies for a package."""

    @abstractmethod
    async def resolve_tree(
        self,
        package_name: str,
        version: str | None = None,
        max_depth: int = 3,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Recursively resolve the full dependency tree."""
