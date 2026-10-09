"""Capability registry for verification providers."""

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()


@dataclass
class VerificationCapability:
    """Represents a verification capability."""

    provider: str
    capability: str
    available: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "capability": self.capability,
            "available": self.available,
            "reason": self.reason,
        }


class CapabilityRegistry:
    """Registry for verification provider capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, list[VerificationCapability]] = {}
        self._initialize_capabilities()

    def _initialize_capabilities(self) -> None:
        """Initialize capabilities based on configuration."""
        # Chip authentication
        self._capabilities["chip_authentication"] = [
            VerificationCapability(
                provider="chip_authentication",
                capability="read_chip",
                available=settings.enable_chip_authentication,
                reason="Enabled in configuration" if settings.enable_chip_authentication else "Disabled in configuration",
            )
        ]

        # Lost/stolen check
        self._capabilities["lost_stolen"] = [
            VerificationCapability(
                provider="lost_stolen_database",
                capability="check_status",
                available=settings.enable_lost_stolen_check,
                reason="Enabled in configuration" if settings.enable_lost_stolen_check else "Disabled in configuration",
            )
        ]

        # System One
        self._capabilities["system_one"] = [
            VerificationCapability(
                provider="system_one",
                capability="decision_model",
                available=settings.system_one_enabled and bool(settings.system_one_api_url),
                reason="Configured with API URL" if settings.system_one_enabled else "Not enabled or no API URL configured",
            )
        ]

        logger.info("Capability registry initialized", capabilities=len(self._capabilities))

    def get_capability(self, provider: str, capability: str) -> VerificationCapability | None:
        """Get a specific capability."""
        caps = self._capabilities.get(provider, [])
        for cap in caps:
            if cap.capability == capability:
                return cap
        return None

    def is_available(self, provider: str, capability: str) -> bool:
        """Check if a capability is available."""
        cap = self.get_capability(provider, capability)
        return cap.available if cap else False

    def list_all_capabilities(self) -> dict[str, list[dict[str, Any]]]:
        """List all capabilities."""
        return {
            provider: [cap.to_dict() for cap in caps] for provider, caps in self._capabilities.items()
        }

    def get_provider_status(self, provider: str) -> dict[str, Any]:
        """Get status of a provider."""
        caps = self._capabilities.get(provider, [])
        return {
            "provider": provider,
            "available": any(cap.available for cap in caps),
            "capabilities": [cap.to_dict() for cap in caps],
        }
