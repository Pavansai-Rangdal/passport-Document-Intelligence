"""Utility functions for generating unique identifiers."""

import secrets
from datetime import datetime


def generate_internal_id(prefix: str = "doc") -> str:
    """Generate a unique internal ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(4)
    return f"{prefix}_{timestamp}_{random_suffix}"


def generate_batch_id() -> str:
    """Generate a unique batch ID."""
    return generate_internal_id("batch")
