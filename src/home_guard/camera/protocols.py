"""Protocol abstractions and interfaces for camera sources and frame consumers."""

from typing import Protocol, runtime_checkable

from home_guard.camera.models import CameraConfig, Frame


@runtime_checkable
class CameraSource(Protocol):
    """Protocol representing a continuous optical or simulated frame generator."""

    @property
    def camera_id(self) -> str:
        """Unique identifier of the camera source."""
        ...

    @property
    def config(self) -> CameraConfig:
        """Immutable configuration object for this source."""
        ...

    @property
    def is_running(self) -> bool:
        """Current operational state of the camera source."""
        ...

    def start(self) -> None:
        """Initialize and start the camera source."""
        ...

    def stop(self) -> None:
        """Stop capturing and release associated resources."""
        ...

    def capture_frame(self) -> Frame | None:
        """Capture or generate the next frame in sequence.

        Returns:
            Frame: The captured frame object.
            None: If the source has stopped or reached end-of-stream.
        """
        ...


@runtime_checkable
class FrameConsumer(Protocol):
    """Protocol representing a downstream sink or consumer of camera frames."""

    def consume_frame(self, frame: Frame) -> None:
        """Process or forward an ingested frame."""
        ...
