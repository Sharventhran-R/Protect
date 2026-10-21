"""Domain models, bounding box contracts, and validation for perception subsystem."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from home_guard.camera.models import FrameMetadata, PixelFormat


class PerceptionError(Exception):
    """Base exception for all perception and detection subsystem errors."""


class InvalidBoundingBoxError(PerceptionError, ValueError):
    """Raised when a bounding box definition or coordinate geometry is invalid."""


class InvalidDetectionError(PerceptionError, ValueError):
    """Raised when a detection observation fails validation."""


class InvalidDetectionResultError(PerceptionError, ValueError):
    """Raised when a detection result payload or frame association fails validation."""


class DetectionErrorCode(StrEnum):
    """Standard error codes for detection failures."""

    MODEL_NOT_INITIALIZED = "model_not_initialized"
    INFERENCE_FAILED = "inference_failed"
    INVALID_FRAME_PAYLOAD = "invalid_frame_payload"
    TIMEOUT = "timeout"
    DEVICE_ERROR = "device_error"
    UNSUPPORTED_PIXEL_FORMAT = "unsupported_pixel_format"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectionErrorDetail:
    """Structured information describing a detection failure."""

    code: DetectionErrorCode | str
    message: str
    exception_type: str | None = None

    def __post_init__(self) -> None:
        """Validate failure details."""
        if isinstance(self.code, DetectionErrorCode):
            pass
        elif isinstance(self.code, str):
            try:
                object.__setattr__(self, "code", DetectionErrorCode(self.code))
            except ValueError:
                object.__setattr__(self, "code", DetectionErrorCode.UNKNOWN)
        else:
            raise InvalidDetectionResultError(
                f"error code must be a DetectionErrorCode or str, got {type(self.code).__name__}"
            )

        if not isinstance(self.message, str) or not self.message.strip():
            raise InvalidDetectionResultError(
                "DetectionErrorDetail message must be a non-empty string."
            )
        object.__setattr__(self, "message", self.message.strip())


@dataclass(frozen=True)
class BoundingBox:
    """Immutable 2D bounding box in absolute image pixel coordinates [x1, y1, x2, y2].

    Follows half-open rectangular geometry where x1, y1 represent the top-left boundary
    and x2, y2 represent the bottom-right boundary. The width is (x2 - x1) and height
    is (y2 - y1), making valid image bounds [0, width] and [0, height].
    """

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        """Validate coordinates and half-open box geometry."""
        for name, val in (("x1", self.x1), ("y1", self.y1), ("x2", self.x2), ("y2", self.y2)):
            if isinstance(val, bool):
                raise InvalidBoundingBoxError(f"{name} cannot be a boolean, got {val!r}")
            if not isinstance(val, (int, float)):
                raise InvalidBoundingBoxError(
                    f"{name} must be a real number, got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise InvalidBoundingBoxError(f"{name} must be a finite number, got {val}")

        if self.x1 < 0.0 or self.y1 < 0.0:
            raise InvalidBoundingBoxError(
                f"Coordinates (x1, y1) must be non-negative, got ({self.x1}, {self.y1})"
            )

        if self.x2 <= self.x1:
            raise InvalidBoundingBoxError(
                f"x2 ({self.x2}) must be strictly greater than x1 ({self.x1}) for positive width."
            )
        if self.y2 <= self.y1:
            raise InvalidBoundingBoxError(
                f"y2 ({self.y2}) must be strictly greater than y1 ({self.y1}) for positive height."
            )

        object.__setattr__(self, "x1", float(self.x1))
        object.__setattr__(self, "y1", float(self.y1))
        object.__setattr__(self, "x2", float(self.x2))
        object.__setattr__(self, "y2", float(self.y2))

    @property
    def width(self) -> float:
        """Width of the bounding box (x2 - x1)."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Height of the bounding box (y2 - y1)."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Area of the bounding box (width * height)."""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """Centroid coordinates (cx, cy) of the bounding box."""
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio (width / height) of the bounding box."""
        return self.width / self.height

    def iou(self, other: BoundingBox) -> float:
        """Calculate the Intersection-over-Union (IoU) with another bounding box.

        Args:
            other: Target BoundingBox to compare with.

        Returns:
            float: IoU value in the range [0.0, 1.0].
        """
        if not isinstance(other, BoundingBox):
            raise TypeError(f"other must be an instance of BoundingBox, got {type(other).__name__}")

        inter_x1 = max(self.x1, other.x1)
        inter_y1 = max(self.y1, other.y1)
        inter_x2 = min(self.x2, other.x2)
        inter_y2 = min(self.y2, other.y2)

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        union_area = self.area + other.area - inter_area
        if union_area <= 0.0:
            return 0.0
        return float(inter_area / union_area)

    def clip_to_image(self, width: int | float, height: int | float) -> BoundingBox:
        """Clip bounding box to image dimensions [0, width] and [0, height].

        Args:
            width: Image width (must be positive).
            height: Image height (must be positive).

        Returns:
            BoundingBox: New clipped bounding box.

        Raises:
            ValueError: If width or height are not positive real numbers.
            InvalidBoundingBoxError: If the box does not have a positive-area intersection
                                     with the image boundary.
        """
        if isinstance(width, bool) or not isinstance(width, (int, float)):
            raise ValueError(f"Image width must be a real number, got {type(width).__name__}")
        if not math.isfinite(width) or width <= 0:
            raise ValueError(f"Image width must be a positive finite number, got {width}")

        if isinstance(height, bool) or not isinstance(height, (int, float)):
            raise ValueError(f"Image height must be a real number, got {type(height).__name__}")
        if not math.isfinite(height) or height <= 0:
            raise ValueError(f"Image height must be a positive finite number, got {height}")

        cx1 = max(0.0, self.x1)
        cy1 = max(0.0, self.y1)
        cx2 = min(float(width), self.x2)
        cy2 = min(float(height), self.y2)

        if cx2 <= cx1 or cy2 <= cy1:
            raise InvalidBoundingBoxError(
                f"BoundingBox ({self.x1}, {self.y1}, {self.x2}, {self.y2}) has no positive-area "
                f"intersection with image dimensions {width}x{height}."
            )

        return BoundingBox(x1=cx1, y1=cy1, x2=cx2, y2=cy2)


@dataclass(frozen=True)
class Detection:
    """An immutable object observation extracted from a frame."""

    class_id: int
    label: str
    confidence: float
    box: BoundingBox

    def __post_init__(self) -> None:
        """Validate detection attributes."""
        if isinstance(self.class_id, bool) or not isinstance(self.class_id, int):
            raise InvalidDetectionError(
                f"class_id must be an integer, got {type(self.class_id).__name__}"
            )
        if self.class_id < 0:
            raise InvalidDetectionError(f"class_id must be non-negative, got {self.class_id}")

        if not isinstance(self.label, str) or not self.label.strip():
            raise InvalidDetectionError(f"label must be a non-empty string, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())

        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise InvalidDetectionError(
                f"confidence must be a float, got {type(self.confidence).__name__}"
            )
        if not math.isfinite(self.confidence):
            raise InvalidDetectionError(
                f"confidence must be a finite number, got {self.confidence}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise InvalidDetectionError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        object.__setattr__(self, "confidence", float(self.confidence))

        if not isinstance(self.box, BoundingBox):
            raise InvalidDetectionError(
                f"box must be an instance of BoundingBox, got {type(self.box).__name__}"
            )


@dataclass(frozen=True, init=False)
class DetectionResult:
    """Immutable inference result for a single camera frame."""

    frame_metadata: FrameMetadata
    detections: tuple[Detection, ...]
    latency_ms: float
    error: DetectionErrorDetail | None

    def __init__(
        self,
        frame_metadata: FrameMetadata | None = None,
        detections: Sequence[Detection] = (),
        latency_ms: float = 0.0,
        error: DetectionErrorDetail | str | None = None,
        *,
        camera_id: str | None = None,
        sequence_number: int | None = None,
        timestamp_ns: int | None = None,
        timestamp_utc: str | None = None,
        width: int | None = None,
        height: int | None = None,
        pixel_format: PixelFormat | None = None,
    ) -> None:
        """Initialize and validate detection result."""
        # 1. Resolve FrameMetadata
        if frame_metadata is None:
            if (
                camera_id is None
                or sequence_number is None
                or timestamp_ns is None
                or timestamp_utc is None
            ):
                raise InvalidDetectionResultError(
                    "Either frame_metadata or complete frame identity fields "
                    "(camera_id, sequence_number, timestamp_ns, timestamp_utc) must be provided."
                )
            meta = FrameMetadata(
                camera_id=camera_id,
                sequence_number=sequence_number,
                timestamp_ns=timestamp_ns,
                timestamp_utc=timestamp_utc,
                width=width if width is not None else 640,
                height=height if height is not None else 480,
                pixel_format=pixel_format if pixel_format is not None else PixelFormat.RGB24,
            )
            object.__setattr__(self, "frame_metadata", meta)
        else:
            if not isinstance(frame_metadata, FrameMetadata):
                raise InvalidDetectionResultError(
                    f"frame_metadata must be an instance of FrameMetadata, "
                    f"got {type(frame_metadata).__name__}"
                )
            # Check for explicit identity field mismatches
            if camera_id is not None and camera_id != frame_metadata.camera_id:
                raise InvalidDetectionResultError(
                    f"Explicit camera_id '{camera_id}' does not match frame_metadata.camera_id "
                    f"'{frame_metadata.camera_id}'."
                )
            if sequence_number is not None and sequence_number != frame_metadata.sequence_number:
                raise InvalidDetectionResultError(
                    f"Explicit sequence_number {sequence_number} does not match "
                    f"frame_metadata.sequence_number {frame_metadata.sequence_number}."
                )
            if timestamp_ns is not None and timestamp_ns != frame_metadata.timestamp_ns:
                raise InvalidDetectionResultError(
                    f"Explicit timestamp_ns {timestamp_ns} does not match "
                    f"frame_metadata.timestamp_ns {frame_metadata.timestamp_ns}."
                )
            if timestamp_utc is not None and timestamp_utc != frame_metadata.timestamp_utc:
                raise InvalidDetectionResultError(
                    f"Explicit timestamp_utc '{timestamp_utc}' does not match "
                    f"frame_metadata.timestamp_utc '{frame_metadata.timestamp_utc}'."
                )
            object.__setattr__(self, "frame_metadata", frame_metadata)

        # 2. Validate latency
        if isinstance(latency_ms, bool) or not isinstance(latency_ms, (int, float)):
            raise InvalidDetectionResultError(
                f"latency_ms must be a real number, got {type(latency_ms).__name__}"
            )
        if not math.isfinite(latency_ms):
            raise InvalidDetectionResultError(
                f"latency_ms must be a finite number, got {latency_ms}"
            )
        if latency_ms < 0.0:
            raise InvalidDetectionResultError(f"latency_ms must be non-negative, got {latency_ms}")
        object.__setattr__(self, "latency_ms", float(latency_ms))

        # 3. Validate detections
        if not isinstance(detections, (tuple, list)):
            raise InvalidDetectionResultError(
                f"detections must be a sequence of Detection objects, "
                f"got {type(detections).__name__}"
            )
        for idx, d in enumerate(detections):
            if not isinstance(d, Detection):
                raise InvalidDetectionResultError(
                    f"detections[{idx}] must be an instance of Detection, got {type(d).__name__}"
                )
        object.__setattr__(self, "detections", tuple(detections))

        # 4. Validate error / failure semantics
        if error is not None:
            if isinstance(error, str):
                error_detail: DetectionErrorDetail | None = DetectionErrorDetail(
                    code=DetectionErrorCode.INFERENCE_FAILED,
                    message=error,
                )
            elif isinstance(error, DetectionErrorDetail):
                error_detail = error
            else:
                raise InvalidDetectionResultError(
                    f"error must be a DetectionErrorDetail or str, got {type(error).__name__}"
                )
            if len(self.detections) > 0:
                raise InvalidDetectionResultError(
                    "A failed DetectionResult (error is not None) cannot contain detections."
                )
            object.__setattr__(self, "error", error_detail)
        else:
            object.__setattr__(self, "error", None)

    @property
    def camera_id(self) -> str:
        """Identifier of the camera source."""
        return self.frame_metadata.camera_id

    @property
    def sequence_number(self) -> int:
        """Monotonic sequence number of the source frame."""
        return self.frame_metadata.sequence_number

    @property
    def timestamp_ns(self) -> int:
        """Monotonic nanosecond timestamp of the source frame."""
        return self.frame_metadata.timestamp_ns

    @property
    def timestamp_utc(self) -> str:
        """ISO 8601 UTC timestamp of the source frame."""
        return self.frame_metadata.timestamp_utc

    @property
    def is_success(self) -> bool:
        """True if detection succeeded without errors."""
        return self.error is None

    @property
    def is_failure(self) -> bool:
        """True if detection experienced an error."""
        return self.error is not None

    @classmethod
    def success(
        cls,
        frame_metadata: FrameMetadata,
        detections: Sequence[Detection] = (),
        latency_ms: float = 0.0,
    ) -> DetectionResult:
        """Factory for a successful detection outcome."""
        return cls(
            frame_metadata=frame_metadata,
            detections=tuple(detections),
            latency_ms=latency_ms,
            error=None,
        )

    @classmethod
    def failure(
        cls,
        frame_metadata: FrameMetadata,
        error: DetectionErrorDetail | str,
        latency_ms: float = 0.0,
    ) -> DetectionResult:
        """Factory for a failed detection outcome."""
        error_detail = (
            error
            if isinstance(error, DetectionErrorDetail)
            else DetectionErrorDetail(code=DetectionErrorCode.INFERENCE_FAILED, message=error)
        )
        return cls(
            frame_metadata=frame_metadata,
            detections=(),
            latency_ms=latency_ms,
            error=error_detail,
        )
