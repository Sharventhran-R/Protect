"""Autonomous Agentic AI Home Guard package.

Simulation-first autonomous intelligent home security system.
"""

from home_guard.camera import (
    CameraConfig,
    CameraManager,
    CameraMetrics,
    CameraSource,
    FileCameraSource,
    Frame,
    FrameBuffer,
    FrameMetadata,
    OverflowPolicy,
    PixelFormat,
    SourceType,
    SyntheticCameraSource,
)
from home_guard.health import HealthStatus, get_health_status

__version__ = "0.1.0"
__all__ = [
    "CameraConfig",
    "CameraManager",
    "CameraMetrics",
    "CameraSource",
    "FileCameraSource",
    "Frame",
    "FrameBuffer",
    "FrameMetadata",
    "HealthStatus",
    "OverflowPolicy",
    "PixelFormat",
    "SourceType",
    "SyntheticCameraSource",
    "__version__",
    "get_health_status",
]
