"""Download statistics tools for depcheck-mcp packages."""

import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import NetworkError, PyPIClient, PyPIError

logger = logging.getLogger(__name__)

# Known popular packages for top downloads (PyPI does not provide a direct top API)
_POPULAR_PACKAGES = [
    "requests", "urllib3", "setuptools", "pip", "wheel", "numpy", "pandas",
    "django", "flask", "fastapi", "sqlalchemy", "pytest", "black", "mypy",
    "httpx", "aiohttp", "tornado", "jinja2", "markupsafe", "cryptography",
    "pydantic", "rich", "typer", "click", "toml", "pyyaml", "packaging",
    "certifi", "charset-normalizer", "idna", "python-dateutil", "six",
    "psycopg2-binary", "pymongo", "redis", "boto3", "botocore", "awscli",
    "pillow", "matplotlib", "scipy", "scikit-learn", "torch", "tensorflow",
    "transformers", "langchain", "openai", "anthropic", "tiktoken",
]


async def get_download_statistics(package_name: str, ecosystem: str = "pypi", period: str = "month") -> dict[str, Any]:
    """Get download statistics for a package.

    Uses pypistats.org API for aggregated stats.

    Args:
        package_name: Name of the package.
        period: Time period ('day', 'week', 'month').

    Returns:
        Dictionary with download statistics.
    """
    try:
        # Try to get stats from pypistats
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"https://pypistats.org/api/packages/{package_name}/recent"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                return {
                    "package_name": package_name,
                    "ecosystem": ecosystem,
                    "period": period,
                    "recent_downloads": {
                        "last_day": data.get("data", {}).get("last_day", 0),
                        "last_week": data.get("data", {}).get("last_week", 0),
                        "last_month": data.get("data", {}).get("last_month", 0),
                    },
                    "source": "pypistats.org",
                }
    except Exception as e:
        logger.warning("pypistats failed for %s: %s", package_name, e)

    # Fallback: return empty stats
    return {
        "package_name": package_name,
        "ecosystem": ecosystem,
        "period": period,
        "recent_downloads": {"last_day": 0, "last_week": 0, "last_month": 0},
        "source": "unavailable",
        "note": "Download statistics are currently unavailable for this package.",
    }


async def get_download_trends(
    package_name: str, ecosystem: str = "pypi", days: int = 180
) -> dict[str, Any]:
    """Get download trends over time for a package.

    Args:
        package_name: Name of the package.
        days: Number of days of history (default: 180).

    Returns:
        Dictionary with trend data.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"https://pypistats.org/api/packages/{package_name}/overall"
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                downloads = data.get("data", [])
                # Sort by date and take last N days
                sorted_downloads = sorted(downloads, key=lambda x: x.get("date", ""), reverse=True)
                recent = sorted_downloads[:days]

                total = sum(d.get("downloads", 0) for d in recent)
                avg_daily = total / len(recent) if recent else 0

                return {
                    "package_name": package_name,
                    "ecosystem": ecosystem,
                    "days": len(recent),
                    "total_downloads": total,
                    "average_daily": round(avg_daily, 2),
                    "trend_data": [
                        {"date": d.get("date"), "downloads": d.get("downloads")}
                        for d in recent[:30]  # Return last 30 data points
                    ],
                    "source": "pypistats.org",
                }
    except Exception as e:
        logger.warning("Trend fetch failed for %s: %s", package_name, e)

    return {
        "package_name": package_name,
        "ecosystem": ecosystem,
        "days": days,
        "total_downloads": 0,
        "average_daily": 0,
        "trend_data": [],
        "source": "unavailable",
        "note": "Trend data is currently unavailable.",
    }


async def get_top_downloaded_packages(
    ecosystem: str = "pypi", period: str = "month", limit: int = 20
) -> dict[str, Any]:
    """Get the most downloaded packages.

    Args:
        period: Time period ('day', 'week', 'month').
        limit: Maximum packages to return (default: 20, max: 50).

    Returns:
        Dictionary with top packages.
    """
    actual_limit = min(limit, 50)
    results = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Sample popular packages and get their stats
        for pkg in _POPULAR_PACKAGES[:actual_limit * 2]:
            try:
                url = f"https://pypistats.org/api/packages/{pkg}/recent"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    recent = data.get("data", {})
                    downloads = recent.get("last_month", 0)
                    results.append({
                        "name": pkg,
                        "downloads": downloads,
                    })
            except Exception:
                continue

    # Sort by downloads
    results.sort(key=lambda x: x["downloads"], reverse=True)

    return {
        "ecosystem": ecosystem,
        "period": period,
        "limit": actual_limit,
        "packages": results[:actual_limit],
        "source": "pypistats.org (sampled)",
        "note": "Results based on sampling known popular packages.",
    }


def register(mcp: FastMCP) -> None:
    """Register stats tools."""
    mcp.tool()(get_download_statistics)
    mcp.tool()(get_download_trends)
    mcp.tool()(get_top_downloaded_packages)
