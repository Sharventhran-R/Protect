"""Camera ingestion and synthetic frame generation subsystem."""

from home_guard.camera.buffer import FrameBuffer
from home_guard.camera.file_source import FileCameraSource
from home_guard.camera.manager import CameraManager
from home_guard.camera.metrics import CameraMetrics
from home_guard.camera.models import (
    CameraConfig,
    CameraError,
    CameraNotFoundError,
    CameraNotRunningError,
    DuplicateCameraError,
    Frame,
    FrameMetadata,
    InvalidCameraConfigError,
    InvalidFrameError,
    MediaFileError,
    OverflowPolicy,
    PixelFormat,
    SourceType,
    VideoDecoderUnavailableError,
)
from home_guard.camera.protocols import CameraSource, FrameConsumer
from home_guard.camera.synthetic import SyntheticCameraSource

__all__ = [
    "CameraConfig",
    "CameraError",
    "CameraManager",
    "CameraMetrics",
    "CameraNotFoundError",
    "CameraNotRunningError",
    "CameraSource",
    "DuplicateCameraError",
    "FileCameraSource",
    "Frame",
    "FrameBuffer",
    "FrameConsumer",
    "FrameMetadata",
    "InvalidCameraConfigError",
    "InvalidFrameError",
    "MediaFileError",
    "OverflowPolicy",
    "PixelFormat",
    "SourceType",
    "SyntheticCameraSource",
    "VideoDecoderUnavailableError",
]
