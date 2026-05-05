"""Python compatibility checking tools."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from packaging.specifiers import SpecifierSet

from pypi_mcp.core import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)

logger = logging.getLogger(__name__)


async def check_python_compatibility(package_name: str, python_version: str) -> dict[str, Any]:
    """Check if a package is compatible with a specific Python version.

    Args:
        package_name: Name of the package.
        python_version: Target Python version (e.g., '3.10', '3.11.4').

    Returns:
        Dictionary with compatibility results.
    """
    try:
        client = PyPIClient()
        raw = await client.get_package_info(package_name)
        await client.close()

        info = raw.get("info", {})
        requires_python = info.get("requires_python", "")

        if not requires_python:
            return {
                "package_name": package_name,
                "python_version": python_version,
                "compatible": True,
                "source": "unspecified (no requires_python)",
                "requires_python": "",
                "note": "Package does not specify Python version requirements.",
            }

        try:
            specifier = SpecifierSet(requires_python)
            compatible = specifier.contains(python_version)
            return {
                "package_name": package_name,
                "python_version": python_version,
                "compatible": compatible,
                "source": "requires_python",
                "requires_python": requires_python,
                "note": f"Package requires Python {requires_python}",
            }
        except Exception:
            return {
                "package_name": package_name,
                "python_version": python_version,
                "compatible": True,
                "source": "parse_error",
                "requires_python": requires_python,
                "note": f"Could not parse requires_python '{requires_python}', assuming compatible.",
            }

    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


async def get_compatible_python_versions(
    package_name: str,
    python_versions: list[str] | None = None,
) -> dict[str, Any]:
    """Check compatibility against multiple Python versions.

    Args:
        package_name: Name of the package.
        python_versions: List of versions to check (defaults to common versions).

    Returns:
        Dictionary with compatibility matrix.
    """
    versions = python_versions or ["3.9", "3.10", "3.11", "3.12", "3.13"]
    results = []

    for pv in versions:
        result = await check_python_compatibility(package_name, pv)
        results.append({
            "python_version": pv,
            "compatible": result.get("compatible", False),
            "requires_python": result.get("requires_python", ""),
        })

    compatible_versions = [r["python_version"] for r in results if r["compatible"]]
    incompatible_versions = [r["python_version"] for r in results if not r["compatible"]]

    return {
        "package_name": package_name,
        "compatible_versions": compatible_versions,
        "incompatible_versions": incompatible_versions,
        "compatibility_rate": len(compatible_versions) / len(versions) if versions else 0,
        "details": results,
    }


def register(mcp: FastMCP) -> None:
    """Register compatibility tools."""
    mcp.tool()(check_python_compatibility)
    mcp.tool()(get_compatible_python_versions)
