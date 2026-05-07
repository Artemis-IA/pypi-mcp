"""OSV (Open Source Vulnerabilities) API client."""

import logging
from typing import Any

import httpx

from .exceptions import NetworkError, OSVError
from .security import AbstractSecurityClient

logger = logging.getLogger(__name__)

OSV_BASE_URL = "https://api.osv.dev/v1"


class OSVClient(AbstractSecurityClient):
    """Async client for OSV vulnerability database."""

    def __init__(self, base_url: str = OSV_BASE_URL, timeout: float = 30.0) -> None:
        """Initialize OSV client.

        Args:
            base_url: Base URL for OSV API.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "User-Agent": "pypi-mcp/0.1.0",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def query_vulnerabilities(
        self, package_name: str, version: str | None = None, ecosystem: str = "PyPI"
    ) -> list[dict[str, Any]]:
        """Query OSV for vulnerabilities affecting a package.

        Args:
            package_name: Name of the package.
            version: Specific version to check (optional).
            ecosystem: Package ecosystem (default: PyPI).

        Returns:
            List of vulnerability entries.
        """
        # OSV API requires ecosystem with proper casing (e.g., "PyPI", not "pypi")
        ecosystem_map = {
            "pypi": "PyPI",
            "npm": "npm",
            "maven": "Maven",
            "go": "Go",
            "cargo": "Cargo",
            "nuget": "NuGet",
        }
        osv_ecosystem = ecosystem_map.get(ecosystem.lower(), ecosystem)

        client = await self._get_client()

        payload: dict[str, Any] = {
            "package": {
                "name": package_name,
                "ecosystem": osv_ecosystem,
            }
        }
        if version:
            payload["version"] = version

        try:
            response = await client.post(
                f"{self.base_url}/query",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("vulns", [])
        except httpx.HTTPStatusError as e:
            raise OSVError(f"OSV API error: {e}", e)
        except httpx.RequestError as e:
            raise NetworkError(f"OSV request failed: {e}", e)
        except Exception as e:
            raise OSVError(f"Unexpected OSV error: {e}", e)

    async def get_vulnerability(self, vuln_id: str) -> dict[str, Any] | None:
        """Get detailed information about a specific vulnerability.

        Args:
            vuln_id: OSV vulnerability ID (e.g., "GHSA-xxx", "CVE-xxx").

        Returns:
            Vulnerability details or None if not found.
        """
        client = await self._get_client()

        try:
            response = await client.get(f"{self.base_url}/vulns/{vuln_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise OSVError(f"OSV API error: {e}", e)
        except httpx.RequestError as e:
            raise NetworkError(f"OSV request failed: {e}", e)
        except Exception as e:
            raise OSVError(f"Unexpected OSV error: {e}", e)
