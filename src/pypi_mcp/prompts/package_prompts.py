"""MCP prompts for PyPI package analysis."""

from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    """Register package analysis prompts."""

    @mcp.prompt()
    def analyze_package_quality(package_name: str, version: str | None = None) -> str:
        """Generate a prompt for comprehensive package quality analysis."""
        v = f" version {version}" if version else ""
        return (
            f"Analyze the quality of the Python package '{package_name}'{v}. "
            f"Consider: maintenance activity, community size, download popularity, "
            f"security track record, documentation quality, test coverage, "
            f"and license compatibility. Provide a summary score and specific recommendations."
        )

    @mcp.prompt()
    def compare_packages(
        packages: list[str],
        use_case: str,
        criteria: list[str] | None = None,
    ) -> str:
        """Generate a prompt for comparing multiple packages."""
        pkgs = ", ".join(f"'{p}'" for p in packages)
        crit = f" Focus on: {', '.join(criteria)}." if criteria else ""
        return (
            f"Compare the following Python packages for the use case '{use_case}': {pkgs}."
            f"{crit} Evaluate based on: features, performance, maintenance, security, "
            f"community support, documentation, and ease of use. Provide a recommendation."
        )

    @mcp.prompt()
    def suggest_alternatives(package_name: str, reason: str) -> str:
        """Generate a prompt for finding package alternatives."""
        return (
            f"Find alternatives to the Python package '{package_name}'. "
            f"Reason for replacement: {reason}. Suggest 3-5 alternatives with "
            f"pros/cons for each, considering: feature parity, maintenance status, "
            f"community adoption, and migration effort."
        )

    @mcp.prompt()
    def resolve_dependency_conflicts(conflicts: list[str]) -> str:
        """Generate a prompt for resolving dependency conflicts."""
        return (
            f"Help resolve the following Python dependency conflicts:\n"
            f"{chr(10).join(f'- {c}' for c in conflicts)}\n\n"
            f"Analyze version constraints, suggest compatible versions, and provide "
            f"a step-by-step resolution strategy. Consider using tools like pip's "
            f"dependency resolver or poetry/uv for automated resolution."
        )

    @mcp.prompt()
    def plan_version_upgrade(
        package_name: str, current_version: str, target_version: str | None = None
    ) -> str:
        """Generate a prompt for planning a version upgrade."""
        target = target_version or "the latest version"
        return (
            f"Plan an upgrade of '{package_name}' from {current_version} to {target}. "
            f"Identify breaking changes, deprecated features, and migration steps. "
            f"Suggest a testing strategy and rollback plan."
        )

    @mcp.prompt()
    def audit_security_risks(packages: list[str]) -> str:
        """Generate a prompt for security risk auditing."""
        pkgs = ", ".join(f"'{p}'" for p in packages)
        return (
            f"Perform a security risk audit on the following Python packages: {pkgs}. "
            f"Check for known vulnerabilities (CVEs/GHSAs), outdated dependencies, "
            f"supply chain risks, and license compliance issues. Provide severity "
            f"ratings and remediation recommendations."
        )

    @mcp.prompt()
    def plan_package_migration(from_package: str, to_package: str) -> str:
        """Generate a prompt for package migration planning."""
        return (
            f"Create a migration plan from '{from_package}' to '{to_package}'. "
            f"Cover: API differences, feature mapping, breaking changes, "
            f"testing strategy, estimated effort, and common pitfalls. "
            f"Provide code examples where helpful."
        )

    @mcp.prompt()
    def check_outdated_packages() -> str:
        """Generate a prompt for checking outdated packages."""
        return (
            "Check the current Python environment for outdated packages. "
            "Identify packages with security vulnerabilities, major version gaps, "
            "and abandoned projects. Prioritize updates by risk level and provide "
            "a recommended update order."
        )

    @mcp.prompt()
    def generate_update_plan(strategy: str = "balanced") -> str:
        """Generate a prompt for creating an update plan."""
        return (
            f"Generate a Python dependency update plan using a '{strategy}' strategy. "
            f"Consider: security patches first, then minor updates, then major updates. "
            f"Suggest testing checkpoints and rollback procedures. Include a timeline "
            f"and risk assessment for each batch of updates."
        )

    @mcp.prompt()
    def find_trending_packages(domain: str | None = None) -> str:
        """Generate a prompt for finding trending packages."""
        domain_str = f" in the '{domain}' domain" if domain else ""
        return (
            f"Discover trending Python packages{domain_str}. Consider: recent GitHub activity, "
            f"PyPI download growth, community buzz, and ecosystem adoption. "
            f"Highlight 5-10 promising packages with justification."
        )
