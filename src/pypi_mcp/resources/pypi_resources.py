"""MCP resources for PyPI package information."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import PyPIClient
from pypi_mcp.core.osv_client import OSVClient

logger = logging.getLogger(__name__)


async def _get_package_metadata(package_name: str) -> dict[str, Any]:
    """Fetch package metadata from PyPI."""
    client = PyPIClient()
    try:
        raw = await client.get_package_info(package_name)
        info = raw.get("info", {})
        return {
            "name": info.get("name"),
            "version": info.get("version"),
            "summary": info.get("summary"),
            "author": info.get("author"),
            "license": info.get("license"),
            "requires_python": info.get("requires_python"),
            "home_page": info.get("home_page"),
            "project_urls": info.get("project_urls"),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        await client.close()


async def _get_package_versions(package_name: str) -> dict[str, Any]:
    """Fetch package versions from PyPI."""
    client = PyPIClient()
    try:
        raw = await client.get_package_info(package_name)
        releases = raw.get("releases", {})
        return {
            "name": package_name,
            "latest": raw.get("info", {}).get("version"),
            "total_versions": len(releases),
            "versions": sorted(releases.keys(), reverse=True),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        await client.close()


async def _get_package_dependencies(package_name: str) -> dict[str, Any]:
    """Fetch package dependencies from PyPI."""
    client = PyPIClient()
    try:
        raw = await client.get_package_info(package_name)
        info = raw.get("info", {})
        return {
            "name": info.get("name"),
            "version": info.get("version"),
            "requires_dist": info.get("requires_dist", []),
            "requires_python": info.get("requires_python"),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        await client.close()


async def _get_package_security(package_name: str) -> dict[str, Any]:
    """Fetch security info from OSV."""
    osv = OSVClient()
    try:
        vulns = await osv.query_vulnerabilities(package_name)
        return {
            "name": package_name,
            "vulnerabilities_count": len(vulns),
            "vulnerabilities": [
                {
                    "id": v.get("id"),
                    "summary": v.get("summary"),
                    "severity": v.get("severity"),
                }
                for v in vulns
            ],
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        await osv.close()


def register(mcp: FastMCP) -> None:
    """Register PyPI resources."""

    @mcp.resource("pypi://package/{package_name}")
    async def package_metadata(package_name: str) -> str:
        """Package metadata from PyPI."""
        data = await _get_package_metadata(package_name)
        import json
        return json.dumps(data, indent=2)

    @mcp.resource("pypi://package/{package_name}/versions")
    async def package_versions(package_name: str) -> str:
        """Package version list from PyPI."""
        data = await _get_package_versions(package_name)
        import json
        return json.dumps(data, indent=2)

    @mcp.resource("pypi://package/{package_name}/dependencies")
    async def package_dependencies(package_name: str) -> str:
        """Package dependencies from PyPI."""
        data = await _get_package_dependencies(package_name)
        import json
        return json.dumps(data, indent=2)

    @mcp.resource("pypi://package/{package_name}/security")
    async def package_security(package_name: str) -> str:
        """Package security report from OSV."""
        data = await _get_package_security(package_name)
        import json
        return json.dumps(data, indent=2)
