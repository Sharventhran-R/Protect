"""Tests for the foundational health module."""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

import home_guard
from home_guard.health import HealthStatus, get_health_status


def test_default_health_status() -> None:
    """Verify that get_health_status returns expected default values."""
    health: HealthStatus = get_health_status()

    assert health.status == "healthy"
    assert health.version == "0.1.0"
    assert health.simulation_mode is True
    assert health.environment == "development"

    # Verify timestamp format is valid ISO 8601
    parsed_time = datetime.fromisoformat(health.timestamp_utc)
    assert parsed_time.tzinfo is not None


def test_custom_health_parameters() -> None:
    """Verify that custom arguments are correctly reflected in HealthStatus."""
    health: HealthStatus = get_health_status(
        simulation_mode=False,
        environment="staging",
    )

    assert health.simulation_mode is False
    assert health.environment == "staging"
    assert health.status == "healthy"


def test_health_status_is_immutable() -> None:
    """Verify that HealthStatus dataclass enforces immutability."""
    health: HealthStatus = get_health_status()

    with pytest.raises(FrozenInstanceError):
        # type ignore is intentional here to test runtime enforcement of immutability
        health.status = "degraded"  # type: ignore[misc]


def test_package_exports_and_version() -> None:
    """Verify package level exports and version consistency."""
    assert hasattr(home_guard, "__version__")
    assert home_guard.__version__ == "0.1.0"
    assert home_guard.get_health_status().version == home_guard.__version__
