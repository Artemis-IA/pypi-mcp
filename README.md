# pypi-mcp

A comprehensive [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for **PyPI package intelligence** — the most complete MCP server for Python package discovery, dependency analysis, security auditing, and version management.

## Features

### Tools (18+)
- **Discovery**: `search_packages`, `get_package_info`, `check_package_exists`
- **Versions**: `get_latest_version`, `get_package_releases`, `list_package_versions`, `compare_versions`
- **Dependencies**: `get_dependencies`, `get_dependency_tree`, `resolve_dependencies` (recursive)
- **Security (OSV)**: `check_vulnerabilities`, `scan_dependency_vulnerabilities`, `security_audit_project`
- **Project Audit**: `check_requirements_txt`, `check_pyproject_toml`, `check_setup_py`
- **Statistics**: `get_download_statistics`, `get_download_trends`, `get_top_downloaded_packages`
- **Compatibility**: `check_python_compatibility`, `get_compatible_python_versions`
- **Environment**: `analyze_environment_dependencies`, `check_outdated_packages`, `generate_update_plan`
- **Download**: `download_package` (wheel/sdist to local directory)
- **Metadata**: `get_package_documentation`, `get_package_changelog`, `get_package_license_info`

### Resources
- `resource://pypi/package/{name}` — package metadata
- `resource://pypi/package/{name}/versions` — version list
- `resource://pypi/package/{name}/dependencies` — dependency tree
- `resource://pypi/package/{name}/security` — vulnerability report
- `resource://pypi/stats/top` — top downloaded packages

### Prompts
- Package quality analysis, comparison, alternatives
- Dependency conflict resolution, version upgrade planning
- Security risk auditing, package migration
- Outdated package detection, update planning
- Trending package discovery

### Transports
- **Streamable HTTP** (default) — for web clients, Claude Code, OpenWebUI
- **stdio** — for Claude Desktop, local MCP clients

## Quick Start

### With uv (recommended)
```bash
uvx pypi-mcp --http --port 8080
```

### With pip
```bash
pip install pypi-mcp
pypi-mcp --http --port 8080
```

### Claude Desktop configuration
```json
{
  "mcpServers": {
    "pypi": {
      "command": "uvx",
      "args": ["pypi-mcp"]
    }
  }
}
```

## Architecture

Built on the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp>=1.6.0`) with:
- Modular tool registration pattern
- Async httpx client with caching and retry
- OSV vulnerability integration
- Extensible registry plugin architecture (future: npm, Maven, Go, Docker)

## License

MIT
