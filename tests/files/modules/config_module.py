"""Config module with functions that might be public API."""

from typing import Any


def parse_config() -> dict[str, Any]:
    """Parse configuration - used by other modules (should stay public)."""
    return {"debug": True, "port": 8080}


def get_default_settings() -> dict[str, str]:
    """Get default settings - used by other modules (should stay public)."""
    return {"theme": "dark", "language": "en"}


def internal_helper() -> str:
    """Internal helper - only used within this module."""
    return "helper"


def validate_config_internal(config: dict[str, Any]) -> bool:
    """Validate config - only used within this module."""
    result = internal_helper()
    return len(config) > 0 and result == "helper"
