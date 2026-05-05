"""Version management tools for PyPI packages."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from packaging.version import Version as PackagingVersion, parse as parse_version

from pypi_mcp.core import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)
from pypi_mcp.core.models import VersionInfo

logger = logging.getLogger(__name__)


async def get_latest_version(package_name: str) -> dict[str, Any]:
    """Get the latest version of a PyPI package.

    Args:
        package_name: Name of the package.

    Returns:
        Dictionary with latest version.
    """
    try:
        client = PyPIClient()
        version = await client.get_latest_version(package_name)
        await client.close()
        return {"package_name": package_name, "latest_version": version}
    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


async def get_package_releases(package_name: str) -> dict[str, Any]:
    """Get all release versions of a package with details.

    Args:
        package_name: Name of the package.

    Returns:
        Dictionary with release information.
    """
    try:
        client = PyPIClient()
        raw = await client.get_package_info(package_name)
        await client.close()

        info = raw.get("info", {})
        releases = raw.get("releases", {})

        # Sort versions properly using packaging
        sorted_versions = sorted(
            releases.keys(),
            key=lambda v: parse_version(v),
            reverse=True,
        )

        version_details = {}
        for version in sorted_versions[:10]:
            files = releases.get(version, [])
            version_details[version] = {
                "file_count": len(files),
                "has_wheel": any(f.get("packagetype") == "bdist_wheel" for f in files),
                "has_source": any(f.get("packagetype") == "sdist" for f in files),
                "upload_time": files[0].get("upload_time", "") if files else "",
            }

        vi = VersionInfo(
            package_name=info.get("name", package_name),
            latest_version=info.get("version", ""),
            total_versions=len(sorted_versions),
            versions=sorted_versions,
            recent_versions=sorted_versions[:20],
            version_details=version_details,
        )
        return {"releases": vi.model_dump()}

    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


async def list_package_versions(package_name: str, limit: int = 50) -> dict[str, Any]:
    """List all available versions for a package.

    Args:
        package_name: Name of the package.
        limit: Maximum versions to return (default: 50, max: 100).

    Returns:
        Dictionary with version list.
    """
    try:
        actual_limit = min(limit, 100)
        client = PyPIClient()
        versions = await client.get_package_versions(package_name)
        await client.close()

        sorted_versions = sorted(versions, key=lambda v: parse_version(v), reverse=True)

        return {
            "package_name": package_name,
            "total_versions": len(sorted_versions),
            "versions": sorted_versions[:actual_limit],
        }

    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


async def compare_versions(
    package_name: str,
    version_a: str,
    version_b: str,
) -> dict[str, Any]:
    """Compare two versions of a package.

    Args:
        package_name: Name of the package.
        version_a: First version to compare.
        version_b: Second version to compare.

    Returns:
        Dictionary with comparison results.
    """
    try:
        va = parse_version(version_a)
        vb = parse_version(version_b)

        if va > vb:
            result = f"{version_a} is newer than {version_b}"
            newer = version_a
            older = version_b
        elif va < vb:
            result = f"{version_b} is newer than {version_a}"
            newer = version_b
            older = version_a
        else:
            result = f"{version_a} and {version_b} are the same version"
            newer = version_a
            older = version_b

        return {
            "package_name": package_name,
            "version_a": version_a,
            "version_b": version_b,
            "newer": newer,
            "older": older,
            "result": result,
            "is_equal": va == vb,
        }

    except Exception as e:
        return {
            "error": f"Version comparison failed: {e}",
            "package_name": package_name,
            "version_a": version_a,
            "version_b": version_b,
        }


def register(mcp: FastMCP) -> None:
    """Register version tools."""
    mcp.tool()(get_latest_version)
    mcp.tool()(get_package_releases)
    mcp.tool()(list_package_versions)
    mcp.tool()(compare_versions)
