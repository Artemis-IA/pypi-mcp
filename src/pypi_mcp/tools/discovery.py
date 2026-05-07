"""Discovery tools for depcheck-mcp packages."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import (
    AbstractRegistryClient,
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)
from pypi_mcp.core.models import PackageInfo


logger = logging.getLogger(__name__)


def _get_registry_client(ecosystem: str) -> AbstractRegistryClient:
    """Get the appropriate registry client for an ecosystem."""
    if ecosystem == "pypi":
        return PyPIClient()
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")


async def search_packages(query: str, ecosystem: str = "pypi", limit: int = 20) -> dict[str, Any]:
    """Search packages by keyword across supported ecosystems.

    Args:
        query: Search keyword (e.g., 'web framework', 'async http').
        ecosystem: Package ecosystem (default: 'pypi').
        limit: Maximum number of results (default: 20).

    Returns:
        Dictionary with search results.
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty", "results": []}

    try:
        client = _get_registry_client(ecosystem)
        results = await client.search_packages(query, limit=limit)
        await client.close()
        return {"query": query, "ecosystem": ecosystem, "count": len(results), "results": results}
    except Exception as e:
        logger.error("Search error: %s", e)
        return {"error": str(e), "query": query, "ecosystem": ecosystem, "results": []}


async def get_package_info_tool(package_name: str, ecosystem: str = "pypi") -> dict[str, Any]:
    """Get comprehensive information about a package.

    Args:
        package_name: Name of the package (e.g., 'requests', 'django').
        ecosystem: Package ecosystem (default: 'pypi').

    Returns:
        Dictionary with package metadata.
    """
    try:
        client = _get_registry_client(ecosystem)
        raw = await client.get_package_info(package_name)
        await client.close()

        info = raw.get("info", {})
        releases = raw.get("releases", {})
        versions = list(releases.keys())

        pkg = PackageInfo(
            ecosystem=ecosystem,
            name=info.get("name", package_name),
            version=info.get("version", ""),
            summary=info.get("summary", ""),
            description=(info.get("description", "")[:500] + "...")
            if len(info.get("description", "")) > 500
            else info.get("description", ""),
            author=info.get("author", ""),
            author_email=info.get("author_email", ""),
            maintainer=info.get("maintainer", ""),
            maintainer_email=info.get("maintainer_email", ""),
            license=info.get("license", ""),
            home_page=info.get("home_page", ""),
            project_url=info.get("project_url", ""),
            requires_python=info.get("requires_python", ""),
            keywords=info.get("keywords", ""),
            classifiers=info.get("classifiers", []),
            requires_dist=info.get("requires_dist", []),
            project_urls=info.get("project_urls", {}),
            total_versions=len(versions),
            available_versions=versions[-10:] if versions else [],
        )
        return {"package": pkg.model_dump()}

    except PyPIError as e:
        logger.error("Registry error for %s: %s", package_name, e)
        return {"error": str(e), "error_type": type(e).__name__, "ecosystem": ecosystem, "package_name": package_name}
    except Exception as e:
        logger.error("Unexpected error for %s: %s", package_name, e)
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "ecosystem": ecosystem,
            "package_name": package_name,
        }


async def check_package_exists(package_name: str, ecosystem: str = "pypi") -> dict[str, Any]:
    """Check if a package exists on the specified registry.

    Args:
        package_name: Name of the package.
        ecosystem: Package ecosystem (default: 'pypi').

    Returns:
        Dictionary with existence status.
    """
    try:
        client = _get_registry_client(ecosystem)
        await client.get_package_info(package_name)
        await client.close()
        return {"package_name": package_name, "ecosystem": ecosystem, "exists": True}
    except PackageNotFoundError:
        return {"package_name": package_name, "ecosystem": ecosystem, "exists": False}
    except Exception as e:
        return {"package_name": package_name, "ecosystem": ecosystem, "exists": False, "error": str(e)}


def register(mcp: FastMCP) -> None:
    """Register discovery tools."""
    mcp.tool()(search_packages)
    mcp.tool()(get_package_info_tool)
    mcp.tool()(check_package_exists)
