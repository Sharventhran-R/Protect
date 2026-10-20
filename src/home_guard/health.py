"""Health and status check foundation for Autonomous Agentic AI Home Guard."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class HealthStatus:
    """Represents the foundational runtime health status of the home guard system."""

    status: str
    version: str
    timestamp_utc: str
    simulation_mode: bool
    environment: str


def get_health_status(
    simulation_mode: bool = True,
    environment: str = "development",
) -> HealthStatus:
    """Retrieve the foundational health status of the system.

    Args:
        simulation_mode: Indicates whether the system is operating in simulation mode.
        environment: The operational runtime environment name.

    Returns:
        HealthStatus: An immutable dataclass containing current health metadata.
    """
    return HealthStatus(
        status="healthy",
        version="0.1.0",
        timestamp_utc=datetime.now(UTC).isoformat(),
        simulation_mode=simulation_mode,
        environment=environment,
    )
