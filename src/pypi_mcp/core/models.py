"""Pydantic models for pypi-mcp."""

from typing import Any

from pydantic import BaseModel, Field


class PackageInfo(BaseModel):
    """Package metadata from PyPI."""

    name: str
    version: str
    summary: str | None = ""
    description: str | None = ""
    author: str | None = ""
    author_email: str | None = ""
    maintainer: str | None = ""
    maintainer_email: str | None = ""
    license: str | None = ""
    home_page: str | None = ""
    project_url: str | None = ""
    requires_python: str | None = ""
    keywords: str | None = ""
    classifiers: list[str] = Field(default_factory=list)
    requires_dist: list[str] | None = Field(default_factory=list)
    project_urls: dict[str, str] | None = Field(default_factory=dict)
    total_versions: int = 0
    available_versions: list[str] = Field(default_factory=list)


class VersionInfo(BaseModel):
    """Version information for a package."""

    package_name: str
    latest_version: str
    total_versions: int
    versions: list[str] = Field(default_factory=list)
    recent_versions: list[str] = Field(default_factory=list)
    version_details: dict[str, Any] = Field(default_factory=dict)


class DependencyInfo(BaseModel):
    """Dependency information for a package."""

    package_name: str
    version: str
    requires_python: str = ""
    runtime_dependencies: list[str] = Field(default_factory=list)
    development_dependencies: list[str] = Field(default_factory=list)
    optional_dependencies: dict[str, list[str]] = Field(default_factory=dict)
    total_dependencies: int = 0
    dependency_summary: dict[str, int] = Field(default_factory=dict)


class DependencyTree(BaseModel):
    """Recursive dependency tree for a package."""

    package_name: str
    python_version: str | None = None
    include_extras: list[str] = Field(default_factory=list)
    include_dev: bool = False
    dependency_tree: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


class DownloadStats(BaseModel):
    """Download statistics for a package."""

    package_name: str
    period: str = "month"
    recent_downloads: dict[str, int] = Field(default_factory=dict)
    trends: dict[str, Any] = Field(default_factory=dict)


class Vulnerability(BaseModel):
    """OSV vulnerability entry."""

    id: str
    summary: str = ""
    details: str = ""
    severity: str = ""
    aliases: list[str] = Field(default_factory=list)
    affected_versions: list[str] = Field(default_factory=list)
    fixed_versions: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    published: str = ""
    modified: str = ""


class SecurityReport(BaseModel):
    """Security audit report for a package or project."""

    package_name: str | None = None
    scanned_packages: int = 0
    vulnerabilities_found: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    summary: str = ""


class PackageHealth(BaseModel):
    """Package health score composite."""

    package_name: str
    score: float = Field(ge=0.0, le=100.0)
    maintenance: float = Field(ge=0.0, le=100.0)
    popularity: float = Field(ge=0.0, le=100.0)
    security: float = Field(ge=0.0, le=100.0)
    community: float = Field(ge=0.0, le=100.0)
    notes: list[str] = Field(default_factory=list)
