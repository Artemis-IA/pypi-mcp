"""ExtensionManager for MCP extensions (SEP-2133)."""

from typing import Any

from .models import ExtensionCapability


class ExtensionManager:
    """Manages server extensions for capability negotiation."""

    _extensions: dict[str, ExtensionCapability] = {}

    @classmethod
    def register(cls, capability: ExtensionCapability) -> None:
        """Register an extension capability."""
        cls._extensions[capability.name] = capability

    @classmethod
    def get(cls, name: str) -> ExtensionCapability | None:
        """Get a registered extension by name."""
        return cls._extensions.get(name)

    @classmethod
    def list_extensions(cls) -> list[ExtensionCapability]:
        """List all registered extensions."""
        return list(cls._extensions.values())

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """Export extensions as a dict for MCP capabilities."""
        return {
            name: {
                "version": cap.version,
                "ecosystems": cap.ecosystems,
                "actions": cap.actions,
                "security_sources": cap.security_sources,
            }
            for name, cap in cls._extensions.items()
        }
