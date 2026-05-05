"""Package download tools."""

import logging
import os
from typing import Any

import aiofiles
import httpx
from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)

logger = logging.getLogger(__name__)


async def download_package(
    package_name: str,
    download_dir: str = "./downloads",
    version: str | None = None,
    prefer_wheel: bool = True,
) -> dict[str, Any]:
    """Download a PyPI package to a local directory.

    Args:
        package_name: Name of the package.
        download_dir: Directory to save files (default: ./downloads).
        version: Specific version (optional, defaults to latest).
        prefer_wheel: Prefer wheel over sdist (default: True).

    Returns:
        Dictionary with download results.
    """
    try:
        client = PyPIClient()
        raw = await client.get_package_info(package_name)
        await client.close()

        info = raw.get("info", {})
        pkg_version = version or info.get("version", "")
        urls = raw.get("urls", [])

        if not urls:
            return {
                "package_name": package_name,
                "version": pkg_version,
                "success": False,
                "error": "No distribution files available",
            }

        # Select file to download
        selected = None
        if prefer_wheel:
            wheels = [u for u in urls if u.get("packagetype") == "bdist_wheel"]
            if wheels:
                selected = wheels[0]
        if not selected:
            sdists = [u for u in urls if u.get("packagetype") == "sdist"]
            if sdists:
                selected = sdists[0]
        if not selected:
            selected = urls[0]

        download_url = selected.get("url", "")
        filename = selected.get("filename", "")

        if not download_url or not filename:
            return {
                "package_name": package_name,
                "version": pkg_version,
                "success": False,
                "error": "Invalid download URL or filename",
            }

        # Ensure download directory exists
        os.makedirs(download_dir, exist_ok=True)
        filepath = os.path.join(download_dir, filename)

        # Download file
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as dl_client:
            response = await dl_client.get(download_url)
            response.raise_for_status()

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(response.content)

        return {
            "package_name": package_name,
            "version": pkg_version,
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "size_bytes": len(response.content),
            "packagetype": selected.get("packagetype", ""),
        }

    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Download failed: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


def register(mcp: FastMCP) -> None:
    """Register download tools."""
    mcp.tool()(download_package)
