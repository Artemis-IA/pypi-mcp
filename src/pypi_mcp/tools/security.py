"""Security audit tools for depcheck-mcp."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import (
    AbstractRegistryClient,
    InvalidPackageNameError,
    NetworkError,
    OSVClient,
    OSVError,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)
from pypi_mcp.core.models import SecurityReport, Vulnerability


def _get_registry_client(ecosystem: str) -> AbstractRegistryClient:
    """Get the appropriate registry client for an ecosystem."""
    if ecosystem == "pypi":
        return PyPIClient()
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")

logger = logging.getLogger(__name__)


async def check_vulnerabilities(
    package_name: str, version: str | None = None, ecosystem: str = "pypi"
) -> dict[str, Any]:
    """Check for known vulnerabilities in a package using OSV.

    Args:
        package_name: Name of the package.
        version: Specific version to check (optional, defaults to latest).
        ecosystem: Package ecosystem (default: 'pypi').

    Returns:
        Dictionary with vulnerability report.
    """
    try:
        # If no version provided, fetch latest
        if not version:
            client = _get_registry_client(ecosystem)
            raw = await client.get_package_info(package_name)
            await client.close()
            version = raw.get("info", {}).get("version", "")

        osv = OSVClient()
        vulns = await osv.query_vulnerabilities(package_name, version, ecosystem=ecosystem.capitalize())
        await osv.close()

        vulnerabilities = []
        critical = high = medium = low = 0

        for v in vulns:
            severity = "UNKNOWN"
            # Extract severity from severity field or database_specific
            if "severity" in v and v["severity"]:
                for s in v["severity"]:
                    if s.get("type") == "CVSS_V3":
                        score = s.get("score", 0)
                        if score >= 9.0:
                            severity = "CRITICAL"
                        elif score >= 7.0:
                            severity = "HIGH"
                        elif score >= 4.0:
                            severity = "MEDIUM"
                        else:
                            severity = "LOW"
                        break

            if severity == "CRITICAL":
                critical += 1
            elif severity == "HIGH":
                high += 1
            elif severity == "MEDIUM":
                medium += 1
            elif severity == "LOW":
                low += 1

            affected = []
            fixed = []
            for affected_entry in v.get("affected", []):
                for r in affected_entry.get("ranges", []):
                    for event in r.get("events", []):
                        if "introduced" in event:
                            affected.append(event["introduced"])
                        if "fixed" in event:
                            fixed.append(event["fixed"])

            vuln = Vulnerability(
                id=v.get("id", ""),
                summary=v.get("summary", ""),
                details=v.get("details", "")[:500],
                severity=severity,
                aliases=v.get("aliases", []),
                affected_versions=affected,
                fixed_versions=fixed,
                references=[ref.get("url", "") for ref in v.get("references", [])],
                published=v.get("published", ""),
                modified=v.get("modified", ""),
            )
            vulnerabilities.append(vuln.model_dump())

        report = SecurityReport(
            ecosystem=ecosystem,
            package_name=package_name,
            scanned_packages=1,
            vulnerabilities_found=len(vulnerabilities),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            vulnerabilities=vulnerabilities,
            summary=f"{len(vulnerabilities)} vulnerabilities found for {package_name}@{version}",
        )
        return {"security_report": report.model_dump()}

    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "ecosystem": ecosystem, "package_name": package_name}
    except OSVError as e:
        return {"error": str(e), "error_type": "OSVError", "ecosystem": ecosystem, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "ecosystem": ecosystem,
            "package_name": package_name,
        }


async def scan_dependency_vulnerabilities(
    package_name: str,
    ecosystem: str = "pypi",
    max_depth: int = 3,
    include_extras: list[str] | None = None,
) -> dict[str, Any]:
    """Deep scan entire dependency tree for vulnerabilities.

    Args:
        package_name: Name of the root package.
        ecosystem: Package ecosystem (default: 'pypi').
        max_depth: Maximum recursion depth (default: 3).
        include_extras: Extra dependency groups to include.

    Returns:
        Dictionary with full security report.
    """
    try:
        client = _get_registry_client(ecosystem)
        osv = OSVClient()
        visited: set[str] = set()
        all_vulns: list[dict[str, Any]] = []
        scanned = 0
        critical = high = medium = low = 0

        async def _scan(name: str, depth: int) -> None:
            nonlocal scanned, critical, high, medium, low
            if depth >= max_depth or name.lower() in visited:
                return
            visited.add(name.lower())

            try:
                raw = await client.get_package_info(name)
            except PackageNotFoundError:
                return

            info = raw.get("info", {})
            version = info.get("version", "")
            scanned += 1

            try:
                vulns = await osv.query_vulnerabilities(name, version, ecosystem=ecosystem.capitalize())
                for v in vulns:
                    severity = "UNKNOWN"
                    if "severity" in v and v["severity"]:
                        for s in v["severity"]:
                            if s.get("type") == "CVSS_V3":
                                score = s.get("score", 0)
                                if score >= 9.0:
                                    severity = "CRITICAL"
                                    critical += 1
                                elif score >= 7.0:
                                    severity = "HIGH"
                                    high += 1
                                elif score >= 4.0:
                                    severity = "MEDIUM"
                                    medium += 1
                                else:
                                    severity = "LOW"
                                    low += 1
                                break

                    all_vulns.append({
                        "package": name,
                        "version": version,
                        "vulnerability_id": v.get("id", ""),
                        "severity": severity,
                        "summary": v.get("summary", ""),
                    })
            except Exception:
                pass  # Continue scanning other packages

            # Resolve children
            requires_dist = info.get("requires_dist", [])
            for dep in requires_dist or []:
                dep_name = dep.split("[")[0].split(";")[0].strip().split(" ")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0].split("~")[0]
                if dep_name and dep_name.lower() not in visited:
                    await _scan(dep_name, depth + 1)

        await _scan(package_name, 0)
        await client.close()
        await osv.close()

        report = SecurityReport(
            ecosystem=ecosystem,
            package_name=package_name,
            scanned_packages=scanned,
            vulnerabilities_found=len(all_vulns),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            vulnerabilities=all_vulns,
            summary=f"Scanned {scanned} packages, found {len(all_vulns)} vulnerabilities in dependency tree of {package_name}",
        )
        return {"security_report": report.model_dump()}

    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "ecosystem": ecosystem,
            "package_name": package_name,
        }


async def security_audit_project(
    requirements: list[str] | None = None,
    pyproject_dependencies: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run a comprehensive security audit on a set of dependencies.

    Args:
        requirements: List of requirements (e.g., ["requests==2.28.1", "flask>=2.0.0"]).
        pyproject_dependencies: Dict of dependencies from pyproject.toml.

    Returns:
        Dictionary with full audit report.
    """
    packages_to_scan: list[tuple[str, str]] = []

    if requirements:
        for req in requirements:
            req = req.strip()
            if not req or req.startswith("#"):
                continue
            # Simple parse: extract name and version
            parts = req.split("==") if "==" in req else req.split(">=") if ">=" in req else req.split("<=") if "<=" in req else [req, ""]
            name = parts[0].strip().split(";")[0].strip()
            version = parts[1].strip() if len(parts) > 1 else ""
            if name:
                packages_to_scan.append((name, version))

    if pyproject_dependencies:
        for name, spec in pyproject_dependencies.items():
            version = spec.strip("^>=~< !").split(",")[0].strip()
            packages_to_scan.append((name, version))

    all_vulns: list[dict[str, Any]] = []
    scanned = 0
    critical = high = medium = low = 0

    try:
        osv = OSVClient()
        for name, version in packages_to_scan:
            try:
                vulns = await osv.query_vulnerabilities(name, version or None)
                scanned += 1
                for v in vulns:
                    severity = "UNKNOWN"
                    if "severity" in v and v["severity"]:
                        for s in v["severity"]:
                            if s.get("type") == "CVSS_V3":
                                score = s.get("score", 0)
                                if score >= 9.0:
                                    severity = "CRITICAL"
                                    critical += 1
                                elif score >= 7.0:
                                    severity = "HIGH"
                                    high += 1
                                elif score >= 4.0:
                                    severity = "MEDIUM"
                                    medium += 1
                                else:
                                    severity = "LOW"
                                    low += 1
                                break
                    all_vulns.append({
                        "package": name,
                        "version": version or "latest",
                        "vulnerability_id": v.get("id", ""),
                        "severity": severity,
                        "summary": v.get("summary", ""),
                    })
            except Exception:
                pass
        await osv.close()

        report = SecurityReport(
            scanned_packages=scanned,
            vulnerabilities_found=len(all_vulns),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            vulnerabilities=all_vulns,
            summary=f"Scanned {scanned} packages, found {len(all_vulns)} vulnerabilities",
        )
        return {"security_report": report.model_dump()}

    except Exception as e:
        return {
            "error": f"Audit failed: {e}",
            "error_type": "UnexpectedError",
        }


def register(mcp: FastMCP) -> None:
    """Register security tools."""
    mcp.tool()(check_vulnerabilities)
    mcp.tool()(scan_dependency_vulnerabilities)
    mcp.tool()(security_audit_project)
