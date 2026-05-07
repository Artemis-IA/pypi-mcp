"""MCP resources for depcheck-mcp multi-ecosystem package information."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import AbstractRegistryClient, OSVClient, PyPIClient

logger = logging.getLogger(__name__)


def _get_client_for_ecosystem(ecosystem: str) -> AbstractRegistryClient:
    """Get the appropriate registry client for an ecosystem."""
    if ecosystem == "pypi":
        return PyPIClient()
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")


async def _get_package_metadata(ecosystem: str, package_name: str) -> dict[str, Any]:
    """Fetch package metadata from the appropriate registry."""
    client = _get_client_for_ecosystem(ecosystem)
    try:
        raw = await client.get_package_info(package_name)
        info = raw.get("info", {})
        return {
            "ecosystem": ecosystem,
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
        return {"ecosystem": ecosystem, "error": str(e)}
    finally:
        await client.close()


async def _get_package_versions(ecosystem: str, package_name: str) -> dict[str, Any]:
    """Fetch package versions from the appropriate registry."""
    client = _get_client_for_ecosystem(ecosystem)
    try:
        raw = await client.get_package_info(package_name)
        releases = raw.get("releases", {})
        return {
            "ecosystem": ecosystem,
            "name": package_name,
            "latest": raw.get("info", {}).get("version"),
            "total_versions": len(releases),
            "versions": sorted(releases.keys(), reverse=True),
        }
    except Exception as e:
        return {"ecosystem": ecosystem, "error": str(e)}
    finally:
        await client.close()


async def _get_package_dependencies(ecosystem: str, package_name: str) -> dict[str, Any]:
    """Fetch package dependencies from the appropriate registry."""
    client = _get_client_for_ecosystem(ecosystem)
    try:
        raw = await client.get_package_info(package_name)
        info = raw.get("info", {})
        return {
            "ecosystem": ecosystem,
            "name": info.get("name"),
            "version": info.get("version"),
            "requires_dist": info.get("requires_dist", []),
            "requires_python": info.get("requires_python"),
        }
    except Exception as e:
        return {"ecosystem": ecosystem, "error": str(e)}
    finally:
        await client.close()


async def _get_package_security(ecosystem: str, package_name: str) -> dict[str, Any]:
    """Fetch security info from OSV."""
    osv = OSVClient()
    try:
        vulns = await osv.query_vulnerabilities(package_name, ecosystem=ecosystem.capitalize())
        return {
            "ecosystem": ecosystem,
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
        return {"ecosystem": ecosystem, "error": str(e)}
    finally:
        await osv.close()


def register(mcp: FastMCP) -> None:
    """Register depcheck resources."""

    @mcp.resource(uri="depcheck://package/{ecosystem}/{package_name}")
    async def package_metadata(ecosystem: str, package_name: str) -> str:
        """Package metadata from the specified ecosystem."""
        data = await _get_package_metadata(ecosystem, package_name)
        import json
        return json.dumps(data, indent=2)

    @mcp.resource(uri="depcheck://package/{ecosystem}/{package_name}/versions")
    async def package_versions(ecosystem: str, package_name: str) -> str:
        """Package version list from the specified ecosystem."""
        data = await _get_package_versions(ecosystem, package_name)
        import json
        return json.dumps(data, indent=2)

    @mcp.resource(uri="depcheck://package/{ecosystem}/{package_name}/dependencies")
    async def package_dependencies(ecosystem: str, package_name: str) -> str:
        """Package dependencies from the specified ecosystem."""
        data = await _get_package_dependencies(ecosystem, package_name)
        import json
        return json.dumps(data, indent=2)

    @mcp.resource(uri="depcheck://package/{ecosystem}/{package_name}/security")
    async def package_security(ecosystem: str, package_name: str) -> str:
        """Package security report from OSV."""
        data = await _get_package_security(ecosystem, package_name)
        import json
        return json.dumps(data, indent=2)
