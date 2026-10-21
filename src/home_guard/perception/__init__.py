"""Perception subsystem: Object detection contracts, validation, and protocols."""

from home_guard.perception.models import (
    BoundingBox,
    Detection,
    DetectionErrorCode,
    DetectionErrorDetail,
    DetectionResult,
    InvalidBoundingBoxError,
    InvalidDetectionError,
    InvalidDetectionResultError,
    PerceptionError,
)
from home_guard.perception.protocols import (
    MultiObjectTracker,
    ObjectDetector,
    TrackingResultProtocol,
)

__all__ = [
    "BoundingBox",
    "Detection",
    "DetectionErrorCode",
    "DetectionErrorDetail",
    "DetectionResult",
    "InvalidBoundingBoxError",
    "InvalidDetectionError",
    "InvalidDetectionResultError",
    "MultiObjectTracker",
    "ObjectDetector",
    "PerceptionError",
    "TrackingResultProtocol",
]
