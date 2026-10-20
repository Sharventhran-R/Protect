"""Domain models, configurations, and frame contracts for camera subsystem."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import numpy as np


class SourceType(StrEnum):
    """Supported camera source types."""

    SYNTHETIC = "synthetic"
    FILE = "file"
    MOCK = "mock"


class PixelFormat(StrEnum):
    """Supported frame pixel representations."""

    RGB24 = "RGB24"
    BGR24 = "BGR24"
    GRAY8 = "GRAY8"


class OverflowPolicy(StrEnum):
    """Buffer behavior when capacity is reached."""

    DROP_OLDEST = "drop_oldest"
    REJECT_NEWEST = "reject_newest"


# --- Custom Domain Exceptions ---


class CameraError(Exception):
    """Base exception for all camera and ingestion subsystem errors."""


class InvalidCameraConfigError(CameraError):
    """Raised when a camera configuration fails validation."""


class InvalidFrameError(CameraError):
    """Raised when a frame payload or metadata fails validation."""


class DuplicateCameraError(CameraError):
    """Raised when registering a camera with an already-existing camera_id."""


class CameraNotFoundError(CameraError):
    """Raised when querying a camera_id that is not registered."""


class CameraNotRunningError(CameraError):
    """Raised when capturing from or interacting with an inactive camera source."""


class VideoDecoderUnavailableError(CameraError):
    """Raised when video file decoding dependencies are unavailable."""


class MediaFileError(CameraError):
    """Raised when a video file is missing, unreadable, or corrupted."""


# --- Configuration and Frame Contracts ---

_CAMERA_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


@dataclass(frozen=True)
class CameraConfig:
    """Immutable configuration for a camera source."""

    camera_id: str
    source_type: SourceType = SourceType.SYNTHETIC
    width: int = 640
    height: int = 480
    fps: float = 30.0
    pixel_format: PixelFormat = PixelFormat.RGB24
    location_name: str = "default"
    file_path: Path | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not self.camera_id or not isinstance(self.camera_id, str):
            raise InvalidCameraConfigError("camera_id must be a non-empty string.")

        if not _CAMERA_ID_PATTERN.match(self.camera_id):
            raise InvalidCameraConfigError(
                f"camera_id '{self.camera_id}' contains invalid characters. "
                "Only alphanumeric characters, underscores, and hyphens are allowed."
            )

        if self.width <= 0 or self.width > 7680:
            raise InvalidCameraConfigError(
                f"width must be between 1 and 7680 pixels, got {self.width}."
            )

        if self.height <= 0 or self.height > 4320:
            raise InvalidCameraConfigError(
                f"height must be between 1 and 4320 pixels, got {self.height}."
            )

        if self.fps <= 0.0 or self.fps > 240.0:
            raise InvalidCameraConfigError(f"fps must be between 0.1 and 240.0, got {self.fps}.")

        if self.source_type == SourceType.FILE and self.file_path is None:
            raise InvalidCameraConfigError("file_path must be specified when source_type is FILE.")


@dataclass(frozen=True)
class FrameMetadata:
    """Immutable metadata accompanying every captured frame."""

    camera_id: str
    sequence_number: int
    timestamp_ns: int
    timestamp_utc: str
    width: int
    height: int
    pixel_format: PixelFormat
    scene_label: str = ""

    def __post_init__(self) -> None:
        """Validate frame metadata fields."""
        if not self.camera_id:
            raise InvalidFrameError("camera_id in FrameMetadata cannot be empty.")

        if self.sequence_number < 0:
            raise InvalidFrameError(
                f"sequence_number must be non-negative, got {self.sequence_number}."
            )

        if self.timestamp_ns <= 0:
            raise InvalidFrameError(f"timestamp_ns must be positive, got {self.timestamp_ns}.")

        if self.width <= 0 or self.height <= 0:
            raise InvalidFrameError(f"Dimensions must be positive, got {self.width}x{self.height}.")

        try:
            datetime.fromisoformat(self.timestamp_utc)
        except (ValueError, TypeError) as exc:
            raise InvalidFrameError(
                f"Invalid ISO 8601 timestamp_utc '{self.timestamp_utc}'."
            ) from exc


@dataclass(frozen=True)
class Frame:
    """Complete captured frame combining validated metadata and raw pixel payload."""

    metadata: FrameMetadata
    payload: np.ndarray

    def __post_init__(self) -> None:
        """Validate payload dimensions and data type."""
        if not isinstance(self.payload, np.ndarray):
            raise InvalidFrameError(
                f"Frame payload must be a numpy.ndarray, got {type(self.payload).__name__}."
            )

        if self.payload.dtype != np.uint8:
            raise InvalidFrameError(f"Frame payload dtype must be uint8, got {self.payload.dtype}.")

        expected_channels = 1 if self.metadata.pixel_format == PixelFormat.GRAY8 else 3

        expected_shape: tuple[int, ...]
        if expected_channels == 1:
            if self.payload.ndim != 2:
                raise InvalidFrameError(
                    f"GRAY8 payload must be 2-dimensional (H, W), got ndim={self.payload.ndim}."
                )
            expected_shape = (self.metadata.height, self.metadata.width)
        else:
            if self.payload.ndim != 3:
                raise InvalidFrameError(
                    f"{self.metadata.pixel_format.value} payload must be 3-dimensional (H, W, C), "
                    f"got ndim={self.payload.ndim}."
                )
            expected_shape = (self.metadata.height, self.metadata.width, expected_channels)

        if self.payload.shape != expected_shape:
            raise InvalidFrameError(
                f"Payload shape {self.payload.shape} does not match metadata {expected_shape}."
            )

    def to_bytes(self) -> bytes:
        """Return raw contiguous byte representation of the frame array."""
        return self.payload.tobytes()

    def __repr__(self) -> str:
        """Provide a safe, concise string representation without dumping raw pixel data."""
        return (
            f"Frame(camera_id='{self.metadata.camera_id}', "
            f"seq={self.metadata.sequence_number}, "
            f"shape={self.payload.shape}, "
            f"dtype={self.payload.dtype}, "
            f"format={self.metadata.pixel_format.value}, "
            f"timestamp_utc='{self.metadata.timestamp_utc}')"
        )
