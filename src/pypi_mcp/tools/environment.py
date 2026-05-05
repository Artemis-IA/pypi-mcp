"""Environment analysis tools for Python projects."""

import logging
import subprocess
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import OSVClient, PackageNotFoundError, PyPIClient, PyPIError

logger = logging.getLogger(__name__)


async def analyze_environment_dependencies(
    requirements: list[str] | None = None,
    pyproject_dependencies: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Analyze the dependencies of a Python project.

    Args:
        requirements: List of requirements.
        pyproject_dependencies: Dict of pyproject.toml dependencies.

    Returns:
        Dictionary with analysis results.
    """
    all_packages: list[dict[str, Any]] = []

    pypi = PyPIClient()
    osv = OSVClient()

    deps_to_check = []
    if requirements:
        for req in requirements:
            req = req.strip()
            if req and not req.startswith("#"):
                # Simple parse
                name = req.split("==")[0].split(">=")[0].split("<")[0].strip().split(";")[0].strip()
                version = ""
                if "==" in req:
                    version = req.split("==", 1)[1].strip().split(",")[0].strip()
                elif ">=" in req:
                    version = req.split(">=", 1)[1].strip().split(",")[0].strip()
                if name:
                    deps_to_check.append((name, version))

    if pyproject_dependencies:
        for name, spec in pyproject_dependencies.items():
            version = spec.strip("^>=~< !").split(",")[0].strip()
            deps_to_check.append((name, version))

    for name, version in deps_to_check:
        try:
            latest = await pypi.get_latest_version(name)
            vulns = await osv.query_vulnerabilities(name, version or latest)

            all_packages.append({
                "name": name,
                "current_version": version or "unspecified",
                "latest_version": latest,
                "up_to_date": (version == latest) if version else False,
                "vulnerabilities": len(vulns),
            })
        except PackageNotFoundError:
            all_packages.append({"name": name, "error": "Package not found"})
        except Exception as e:
            all_packages.append({"name": name, "error": str(e)})

    await pypi.close()
    await osv.close()

    outdated = [p for p in all_packages if p.get("up_to_date") is False]
    vulnerable = [p for p in all_packages if p.get("vulnerabilities", 0) > 0]

    return {
        "total_packages": len(all_packages),
        "outdated_count": len(outdated),
        "vulnerable_count": len(vulnerable),
        "outdated": outdated,
        "vulnerable": vulnerable,
        "packages": all_packages,
    }


async def check_outdated_packages(
    requirements: list[str] | None = None,
    pyproject_dependencies: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Check which packages in a project are outdated.

    Args:
        requirements: List of requirements.
        pyproject_dependencies: Dict of pyproject.toml dependencies.

    Returns:
        Dictionary with outdated packages.
    """
    result = await analyze_environment_dependencies(
        requirements=requirements,
        pyproject_dependencies=pyproject_dependencies,
    )
    return {
        "outdated_count": result["outdated_count"],
        "outdated": result["outdated"],
        "vulnerable_count": result["vulnerable_count"],
        "vulnerable": result["vulnerable"],
    }


async def generate_update_plan(
    requirements: list[str] | None = None,
    pyproject_dependencies: dict[str, str] | None = None,
    strategy: str = "balanced",
) -> dict[str, Any]:
    """Generate an update plan for project dependencies.

    Args:
        requirements: List of requirements.
        pyproject_dependencies: Dict of pyproject.toml dependencies.
        strategy: Update strategy ('conservative', 'balanced', 'aggressive').

    Returns:
        Dictionary with update recommendations.
    """
    result = await analyze_environment_dependencies(
        requirements=requirements,
        pyproject_dependencies=pyproject_dependencies,
    )

    outdated = result.get("outdated", [])
    vulnerable = result.get("vulnerable", [])

    # Prioritize: vulnerable first, then outdated
    priority_updates = []
    seen = set()

    for pkg in vulnerable:
        name = pkg.get("name", "")
        if name not in seen:
            seen.add(name)
            priority_updates.append({
                "name": name,
                "current": pkg.get("current_version", ""),
                "target": pkg.get("latest_version", ""),
                "priority": "critical",
                "reason": "security vulnerability",
            })

    for pkg in outdated:
        name = pkg.get("name", "")
        if name not in seen:
            seen.add(name)
            priority_updates.append({
                "name": name,
                "current": pkg.get("current_version", ""),
                "target": pkg.get("latest_version", ""),
                "priority": "normal",
                "reason": "outdated",
            })

    return {
        "strategy": strategy,
        "total_updates": len(priority_updates),
        "critical_updates": len([u for u in priority_updates if u["priority"] == "critical"]),
        "normal_updates": len([u for u in priority_updates if u["priority"] == "normal"]),
        "recommendations": priority_updates,
        "note": f"Strategy: {strategy}. Critical updates (security) should be applied first.",
    }


def register(mcp: FastMCP) -> None:
    """Register environment tools."""
    mcp.tool()(analyze_environment_dependencies)
    mcp.tool()(check_outdated_packages)
    mcp.tool()(generate_update_plan)
