"""depcheck-mcp server — comprehensive MCP server for multi-ecosystem dependency intelligence."""

import argparse
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger("depcheck_mcp")


@asynccontextmanager
async def _server_lifespan(_server: FastMCP) -> AsyncIterator[None]:
    """Lightweight lifespan for startup/shutdown."""
    logger.info("depcheck-mcp server starting...")
    yield
    logger.info("depcheck-mcp server shutting down...")


_mcp_instructions = """\
You are a multi-ecosystem dependency intelligence assistant. Use the available tools to help users discover,
analyze, and manage dependencies across PyPI, npm, Maven, and more.

## Available Tool Categories

### Discovery
- `search_packages` — Search packages by keyword (supports ecosystem)
- `get_package_info` — Get comprehensive package metadata (supports ecosystem)
- `check_package_exists` — Verify package existence

### Versions
- `get_latest_version` — Latest available version
- `get_package_releases` — All releases with details
- `list_package_versions` — List versions
- `compare_versions` — Compare two versions

### Dependencies
- `get_dependencies` — Direct dependencies
- `get_dependency_tree` — Recursive dependency tree
- `resolve_dependencies` — Full dependency resolution

### Security
- `check_vulnerabilities` — OSV vulnerability scan for a package
- `scan_dependency_vulnerabilities` — Deep scan of dependency tree
- `security_audit_project` — Audit a set of dependencies

### Project Audit
- `check_requirements_txt` — Audit requirements.txt (PyPI)
- `check_pyproject_toml` — Audit pyproject.toml dependencies (PyPI)
- `check_setup_py` — Audit setup.py dependencies (PyPI)

### Statistics
- `get_download_statistics` — Download counts
- `get_download_trends` — Time series trends
- `get_top_downloaded_packages` — Most popular packages

### Compatibility
- `check_python_compatibility` — Check Python version compatibility
- `get_compatible_python_versions` — Multi-version compatibility matrix

### Environment
- `analyze_environment_dependencies` — Analyze project dependencies
- `check_outdated_packages` — Find outdated packages
- `generate_update_plan` — Generate update recommendations

### Download
- `download_package` — Download package to local directory

## Resources
- `depcheck://package/{ecosystem}/{name}` — Package metadata
- `depcheck://package/{ecosystem}/{name}/versions` — Version list
- `depcheck://package/{ecosystem}/{name}/dependencies` — Dependencies
- `depcheck://package/{ecosystem}/{name}/security` — Security report

## Workflow Guidelines
- Always prefer tools over web search for registry data
- Specify ecosystem when calling tools (default: pypi)
- For security questions, use OSV-based security tools first
- For dependency analysis, use tree/resolution tools
- For project audits, use audit tools with the actual dependency files
- Return structured, actionable information
"""

mcp = FastMCP(
    name="depcheck-mcp",
    debug=False,
    instructions=_mcp_instructions,
    stateless_http=True,
    streamable_http_path="/mcp",
    lifespan=_server_lifespan,
)

# Register depcheck extension (SEP-2133)
from pypi_mcp.core import ExtensionManager, ExtensionCapability

ExtensionManager.register(
    ExtensionCapability(
        name="depcheck.v1",
        version="1.0.0",
        ecosystems=["pypi", "npm"],
        actions=["read", "audit", "update", "rollback"],
        security_sources=["osv", "ghsa", "npm-audit"],
    )
)


# Register tool modules
from pypi_mcp.tools import (
    action,
    audit,
    compatibility,
    dependencies,
    discovery,
    download,
    environment,
    security,
    stats,
    versions,
)
from pypi_mcp.resources import pypi_resources
from pypi_mcp.prompts import package_prompts

discovery.register(mcp)
versions.register(mcp)
dependencies.register(mcp)
security.register(mcp)
audit.register(mcp)
stats.register(mcp)
compatibility.register(mcp)
download.register(mcp)
environment.register(mcp)
action.register(mcp)
pypi_resources.register(mcp)
package_prompts.register(mcp)


def main() -> None:
    """CLI entry point for pypi-mcp server."""
    parser = argparse.ArgumentParser(
        description="depcheck-mcp: Comprehensive MCP server for multi-ecosystem dependency intelligence",
    )
    parser.add_argument(
        "--stdio", action="store_true", help="Use stdio transport (default: HTTP)"
    )
    parser.add_argument(
        "--http", action="store_true", help="Use Streamable HTTP transport (default)"
    )
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for HTTP server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        mcp.debug = True
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    if args.stdio:
        mcp.run()
    else:
        import uvicorn
        import uvicorn.config

        uvicorn.config.LOGGING_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {"handlers": ["default"], "level": "INFO"},
        }

        async def _health(_request):  # type: ignore[no-untyped-def]
            return JSONResponse({"status": "ok", "server": "depcheck-mcp"})

        app = mcp.streamable_http_app()
        app.router.routes.append(Route("/health", _health, methods=["GET"]))

        logger.info("Starting depcheck-mcp HTTP server on %s:%d", args.host, args.port)
        uvicorn.run(app, host=args.host, port=args.port, log_config=uvicorn.config.LOGGING_CONFIG)


if __name__ == "__main__":
    main()
