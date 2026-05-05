"""Custom exceptions for pypi-mcp."""


class PyPIError(Exception):
    """Base exception for PyPI-related errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class PackageNotFoundError(PyPIError):
    """Raised when a package is not found on PyPI."""

    def __init__(self, package_name: str, cause: Exception | None = None) -> None:
        super().__init__(f"Package '{package_name}' not found on PyPI", cause)
        self.package_name = package_name


class InvalidPackageNameError(PyPIError):
    """Raised when a package name is invalid."""

    def __init__(self, package_name: str, cause: Exception | None = None) -> None:
        super().__init__(f"Invalid package name: '{package_name}'", cause)
        self.package_name = package_name


class NetworkError(PyPIError):
    """Raised for network-related errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, cause)


class RateLimitError(PyPIError):
    """Raised when PyPI rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None, cause: Exception | None = None) -> None:
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f". Retry after {retry_after} seconds."
        super().__init__(msg, cause)
        self.retry_after = retry_after


class PyPIServerError(PyPIError):
    """Raised for PyPI server errors (5xx)."""

    def __init__(
        self, status_code: int, message: str = "PyPI server error", cause: Exception | None = None
    ) -> None:
        super().__init__(f"{message} (HTTP {status_code})", cause)
        self.status_code = status_code


class OSVError(Exception):
    """Raised for OSV API errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class CacheError(Exception):
    """Raised for cache-related errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause
