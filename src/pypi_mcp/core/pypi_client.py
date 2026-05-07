"""Async PyPI API client with caching and retry logic."""

import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote

import httpx

from .cache import TTLCache
from .exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIServerError,
    RateLimitError,
)
from .registry import AbstractRegistryClient

logger = logging.getLogger(__name__)


class PyPIClient(AbstractRegistryClient):
    """Async client for PyPI JSON API."""

    ecosystem: str = "pypi"

    def __init__(
        self,
        base_url: str = "https://pypi.org/pypi",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize PyPI client.

        Args:
            base_url: Base URL for PyPI API.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache: TTLCache[dict[str, Any]] = TTLCache(default_ttl=300.0)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "User-Agent": "pypi-mcp/0.1.0",
                    "Accept": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _validate_package_name(self, package_name: str) -> str:
        """Validate and normalize package name.

        Args:
            package_name: Package name to validate.

        Returns:
            Normalized package name.

        Raises:
            InvalidPackageNameError: If package name is invalid.
        """
        if not package_name or not package_name.strip():
            raise InvalidPackageNameError(package_name)

        normalized = re.sub(r"[-_.]+", "-", package_name.lower())

        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$", package_name):
            raise InvalidPackageNameError(package_name)

        return normalized

    async def _make_request(self, url: str) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            url: URL to request.

        Returns:
            JSON response data.

        Raises:
            NetworkError: For network-related errors.
            PackageNotFoundError: When package is not found.
            RateLimitError: When rate limit is exceeded.
            PyPIServerError: For server errors.
        """
        client = await self._get_client()
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug("Requesting %s (attempt %d)", url, attempt + 1)
                response = await client.get(url)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    package_name = url.split("/")[-2] if "/" in url else "unknown"
                    raise PackageNotFoundError(package_name)
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_after_int = int(retry_after) if retry_after else None
                    raise RateLimitError(retry_after_int)
                elif response.status_code >= 500:
                    raise PyPIServerError(response.status_code)
                else:
                    raise PyPIServerError(
                        response.status_code, f"Unexpected status: {response.status_code}"
                    )

            except httpx.TimeoutException as e:
                last_exception = NetworkError(f"Request timeout: {e}", e)
            except httpx.NetworkError as e:
                last_exception = NetworkError(f"Network error: {e}", e)
            except (PackageNotFoundError, RateLimitError, PyPIServerError):
                raise
            except Exception as e:
                last_exception = NetworkError(f"Unexpected error: {e}", e)

            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2**attempt))

        raise last_exception

    async def get_package_info(self, package_name: str) -> dict[str, Any]:
        """Get comprehensive package information from PyPI.

        Args:
            package_name: Name of the package to query.

        Returns:
            Raw package data from PyPI API.
        """
        normalized = self._validate_package_name(package_name)
        cache_key = f"info:{normalized}"

        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Cache hit for package info: %s", normalized)
            return cached

        url = f"{self.base_url}/{quote(normalized)}/json"
        data = await self._make_request(url)
        self.cache.set(cache_key, data)
        return data

    async def get_package_versions(self, package_name: str) -> list[str]:
        """Get list of available versions for a package.

        Args:
            package_name: Name of the package.

        Returns:
            List of version strings (sorted, latest first).
        """
        package_info = await self.get_package_info(package_name)
        releases = package_info.get("releases", {})
        return list(releases.keys())

    async def get_latest_version(self, package_name: str) -> str:
        """Get the latest version of a package.

        Args:
            package_name: Name of the package.

        Returns:
            Latest version string.
        """
        package_info = await self.get_package_info(package_name)
        return package_info.get("info", {}).get("version", "")

    async def search_packages(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search PyPI packages by keyword using the search API.

        Args:
            query: Search keyword.
            limit: Maximum results to return.

        Returns:
            List of package search results.
        """
        cache_key = f"search:{query}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        client = await self._get_client()
        # Use PyPI's simple index which lists all packages
        simple_url = "https://pypi.org/simple/"
        try:
            response = await client.get(simple_url, headers={"Accept": "text/html"})
            if response.status_code == 200:
                html = response.text
                matches = []
                query_lower = query.lower()
                # Parse simple index HTML for matching package names
                # PyPI simple index uses standard HTML: <a href="/simple/package-name/">package-name</a>
                import re
                # Pattern for HTML links
                pattern = r'<a href="/simple/([^/]+)/">([^<]+)</a>'
                for match in re.finditer(pattern, html):
                    pkg_name = match.group(2)
                    if pkg_name and query_lower in pkg_name.lower():
                        matches.append({
                            "name": pkg_name,
                            "url": f"https://pypi.org/project/{pkg_name}/",
                        })
                        if len(matches) >= limit:
                            break
                self.cache.set(cache_key, matches, ttl=60.0)
                return matches
        except Exception as e:
            logger.warning("PyPI simple index search failed: %s", e)

        # Fallback: return empty list
        return []

    async def get_versions(self, package_name: str) -> list[str]:
        """Fetch all available versions (alias for get_package_versions)."""
        return await self.get_package_versions(package_name)

    async def get_download_stats(self, package_name: str, period: str = "month") -> dict[str, Any]:
        """Fetch download statistics for a package (PyPI doesn't expose this publicly)."""
        return {"package_name": package_name, "period": period, "downloads": None, "note": "PyPI does not expose public download stats via API"}

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self.cache.clear()
        logger.debug("Cache cleared")
