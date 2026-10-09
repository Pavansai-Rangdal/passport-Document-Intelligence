"""Policy version management."""

from typing import Any


class PolicyVersion:
    """Represents a policy version."""

    def __init__(self, version: str, description: str, rules: list[str]) -> None:
        self.version = version
        self.description = description
        self.rules = rules

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "description": self.description,
            "rules": self.rules,
        }


class PolicyVersions:
    """Registry of policy versions."""

    CURRENT_VERSION = "1.0"

    VERSIONS = {
        "1.0": PolicyVersion(
            version="1.0",
            description="Initial policy with deterministic rules",
            rules=[
                "critical_validation_errors_fail",
                "system_one_high_confidence_fail",
                "system_one_review_recommendation",
                "system_one_low_confidence",
                "validation_warnings_review",
                "insufficient_mrz_data",
                "all_validations_pass",
            ],
        )
    }

    @classmethod
    def get_current(cls) -> PolicyVersion:
        """Get current policy version."""
        return cls.VERSIONS[cls.CURRENT_VERSION]

    @classmethod
    def get_version(cls, version: str) -> PolicyVersion | None:
        """Get specific policy version."""
        return cls.VERSIONS.get(version)

    @classmethod
    def list_versions(cls) -> list[str]:
        """List all available versions."""
        return list(cls.VERSIONS.keys())
