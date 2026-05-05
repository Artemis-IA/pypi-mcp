"""Dependency analysis tools for PyPI packages."""

import logging
from typing import Any, Union

from mcp.server.fastmcp import FastMCP

from pypi_mcp.core import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIClient,
    PyPIError,
)
from pypi_mcp.core.models import DependencyInfo

logger = logging.getLogger(__name__)


def _parse_requires_dist(requires_dist: list[str] | None) -> dict[str, Any]:
    """Parse requires_dist into categorized dependencies."""
    runtime = []
    dev = []
    extras: dict[str, list[str]] = {}

    for dep in requires_dist or []:
        if not dep:
            continue

        dep_str = dep.strip()
        lower = dep_str.lower()

        # Parse extras: dep_name; extra == "extra_name"
        if "extra ==" in lower or "extra==" in lower:
            # Extract extra name
            parts = dep_str.split(";")
            dep_name = parts[0].strip()
            for part in parts[1:]:
                if "extra ==" in part or "extra==" in part:
                    extra_match = part.split("extra ==")[-1].split("extra==")[-1]
                    extra_name = extra_match.strip().strip('"\'')
                    if extra_name:
                        extras.setdefault(extra_name, []).append(dep_name)
        elif any(marker in lower for marker in ["dev", "test", "pytest", "mypy", "lint", "coverage"]):
            dev.append(dep_str)
        else:
            runtime.append(dep_str)

    return {
        "runtime": runtime,
        "development": dev,
        "extras": extras,
        "total": len(requires_dist or []),
    }


async def get_dependencies(package_name: str, version: str | None = None) -> dict[str, Any]:
    """Get dependency information for a PyPI package.

    Args:
        package_name: Name of the package.
        version: Specific version (optional, defaults to latest).

    Returns:
        Dictionary with dependency information.
    """
    try:
        client = PyPIClient()
        raw = await client.get_package_info(package_name)
        await client.close()

        info = raw.get("info", {})
        requires_dist = info.get("requires_dist", [])
        parsed = _parse_requires_dist(requires_dist)

        dep_info = DependencyInfo(
            package_name=info.get("name", package_name),
            version=info.get("version", ""),
            requires_python=info.get("requires_python", ""),
            runtime_dependencies=parsed["runtime"],
            development_dependencies=parsed["development"],
            optional_dependencies=parsed["extras"],
            total_dependencies=parsed["total"],
            dependency_summary={
                "runtime_count": len(parsed["runtime"]),
                "dev_count": len(parsed["development"]),
                "optional_groups": len(parsed["extras"]),
                "total_optional": sum(len(v) for v in parsed["extras"].values()),
            },
        )
        return {"dependencies": dep_info.model_dump()}

    except PyPIError as e:
        return {"error": str(e), "error_type": type(e).__name__, "package_name": package_name}
    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


async def get_dependency_tree(
    package_name: str,
    max_depth: int = 3,
    python_version: str | None = None,
) -> dict[str, Any]:
    """Get a dependency tree for a package.

    Args:
        package_name: Name of the root package.
        max_depth: Maximum recursion depth (default: 3).
        python_version: Target Python version for filtering (optional).

    Returns:
        Dictionary with dependency tree.
    """
    try:
        client = PyPIClient()
        visited: set[str] = set()
        tree: dict[str, Any] = {}

        async def _resolve(name: str, depth: int) -> dict[str, Any] | None:
            if depth >= max_depth or name.lower() in visited:
                return None
            visited.add(name.lower())

            try:
                raw = await client.get_package_info(name)
            except PackageNotFoundError:
                return None

            info = raw.get("info", {})
            requires_dist = info.get("requires_dist", [])
            parsed = _parse_requires_dist(requires_dist)

            node = {
                "name": info.get("name", name),
                "version": info.get("version", ""),
                "requires_python": info.get("requires_python", ""),
                "dependencies": {
                    "runtime": parsed["runtime"],
                    "development": parsed["development"],
                },
                "children": {},
            }

            # Resolve runtime children
            for dep in parsed["runtime"][:10]:  # Limit to prevent explosion
                dep_name = dep.split("[")[0].split(";")[0].strip().split(" ")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0].split("~")[0]
                if dep_name and dep_name.lower() not in visited:
                    child = await _resolve(dep_name, depth + 1)
                    if child:
                        node["children"][dep_name] = child

            return node

        root = await _resolve(package_name, 0)
        await client.close()

        if root is None:
            return {"error": f"Could not resolve package: {package_name}", "package_name": package_name}

        return {
            "package_name": package_name,
            "max_depth": max_depth,
            "python_version": python_version,
            "tree": root,
            "total_packages": len(visited),
        }

    except Exception as e:
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


async def resolve_dependencies(
    package_name: str,
    python_version: Any = None,
    include_extras: list[str] | None = None,
    max_depth: int = 5,
) -> dict[str, Any]:
    """Resolve all dependencies recursively for a package.

    Args:
        package_name: Name of the root package.
        python_version: Target Python version (optional).
        include_extras: Extra dependency groups to include (optional).
        max_depth: Maximum recursion depth (default: 5).

    Returns:
        Dictionary with resolved dependency tree.
    """
    # Convert python_version to string if it's a number
    if python_version is not None and not isinstance(python_version, str):
        python_version = str(python_version)
    return await get_dependency_tree(package_name, max_depth=max_depth, python_version=python_version)


def register(mcp: FastMCP) -> None:
    """Register dependency tools."""
    mcp.tool()(get_dependencies)
    mcp.tool()(get_dependency_tree)
    mcp.tool()(resolve_dependencies)
