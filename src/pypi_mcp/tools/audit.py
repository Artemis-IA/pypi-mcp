"""Project audit tools for requirements.txt, pyproject.toml, setup.py."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import (
    OSVClient,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)

logger = logging.getLogger(__name__)


def _parse_requirement_line(line: str) -> tuple[str, str] | None:
    """Parse a single requirement line."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Handle -e / --editable lines
    if line.startswith("-e ") or line.startswith("--editable "):
        return None

    # Handle -r / -c lines
    if line.startswith("-r ") or line.startswith("-c "):
        return None

    # Extract name and version
    # Remove markers after ;
    if ";" in line:
        line = line.split(";")[0].strip()

    # Handle extras [extra]
    if "[" in line:
        name_part = line.split("[")[0].strip()
        rest = line.split("[", 1)[1]
        # Find the closing ]
        bracket_end = rest.find("]")
        if bracket_end >= 0:
            line = name_part + rest[bracket_end + 1:].strip()
        else:
            line = name_part

    # Extract version specifiers
    specifiers = ["==", ">=", "<=", ">", "<", "!=", "~=", "^"]
    name = line.strip()
    version = ""

    for spec in specifiers:
        if spec in line:
            parts = line.split(spec, 1)
            name = parts[0].strip()
            version = parts[1].strip().split(",")[0].strip()
            break

    if not name:
        return None

    return (name, version)


async def check_requirements_txt(requirements: list[str]) -> dict[str, Any]:
    """Audit a requirements.txt content for outdated packages and vulnerabilities.

    Args:
        requirements: List of requirement lines.

    Returns:
        Dictionary with audit results.
    """
    packages: list[dict[str, Any]] = []
    outdated: list[dict[str, Any]] = []

    pypi = PyPIClient()
    osv = OSVClient()

    for line in requirements:
        parsed = _parse_requirement_line(line)
        if not parsed:
            continue

        name, version = parsed
        try:
            latest = await pypi.get_latest_version(name)
            vulns = await osv.query_vulnerabilities(name, version or latest)

            pkg_info = {
                "name": name,
                "current_version": version or "unspecified",
                "latest_version": latest,
                "vulnerabilities": len(vulns),
            }

            if version and latest and version != latest:
                outdated.append(pkg_info)

            packages.append(pkg_info)
        except PackageNotFoundError:
            packages.append({"name": name, "error": "Package not found on PyPI"})
        except Exception as e:
            packages.append({"name": name, "error": str(e)})

    await pypi.close()
    await osv.close()

    return {
        "total_packages": len(packages),
        "outdated_packages": len(outdated),
        "outdated": outdated,
        "packages": packages,
    }


async def check_pyproject_toml(
    dependencies: dict[str, str],
    optional_dependencies: dict[str, dict[str, str]] | None = None,
    dev_dependencies: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Audit pyproject.toml dependencies.

    Args:
        dependencies: Main dependencies dict {name: version_spec}.
        optional_dependencies: Optional dependency groups.
        dev_dependencies: Dev dependencies dict.

    Returns:
        Dictionary with audit results.
    """
    all_deps = dict(dependencies)
    if optional_dependencies:
        for group, deps in optional_dependencies.items():
            for name, spec in deps.items():
                all_deps[f"{name} (optional:{group})"] = spec
    if dev_dependencies:
        for name, spec in dev_dependencies.items():
            all_deps[f"{name} (dev)"] = spec

    packages: list[dict[str, Any]] = []
    outdated: list[dict[str, Any]] = []

    pypi = PyPIClient()
    osv = OSVClient()

    for raw_name, spec in all_deps.items():
        name = raw_name.split(" (")[0].strip()
        version = spec.strip("^>=~< !").split(",")[0].strip()

        try:
            latest = await pypi.get_latest_version(name)
            vulns = await osv.query_vulnerabilities(name, version or latest)

            pkg_info = {
                "name": name,
                "spec": spec,
                "latest_version": latest,
                "vulnerabilities": len(vulns),
            }

            if version and latest and version != latest:
                outdated.append(pkg_info)

            packages.append(pkg_info)
        except PackageNotFoundError:
            packages.append({"name": name, "error": "Package not found on PyPI"})
        except Exception as e:
            packages.append({"name": name, "error": str(e)})

    await pypi.close()
    await osv.close()

    return {
        "total_packages": len(packages),
        "outdated_packages": len(outdated),
        "outdated": outdated,
        "packages": packages,
    }


async def check_setup_py(dependencies: list[str]) -> dict[str, Any]:
    """Audit setup.py install_requires dependencies.

    Args:
        dependencies: List of dependency strings.

    Returns:
        Dictionary with audit results.
    """
    return await check_requirements_txt(dependencies)


def register(mcp: FastMCP) -> None:
    """Register audit tools."""
    mcp.tool()(check_requirements_txt)
    mcp.tool()(check_pyproject_toml)
    mcp.tool()(check_setup_py)
