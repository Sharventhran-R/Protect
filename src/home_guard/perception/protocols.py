"""Protocol abstractions and interfaces for perception and tracking subsystems."""

from typing import Protocol, runtime_checkable

from home_guard.camera.models import Frame
from home_guard.perception.models import DetectionResult


@runtime_checkable
class TrackingResultProtocol(Protocol):
    """Forward-compatible protocol representing a multi-object tracking result.

    The concrete TrackingResult domain model and tracked object contracts will be
    implemented in Phase 2.3. This protocol defines the minimal required public
    interface for Phase 2.1 typing without speculative dependency imports.
    """

    @property
    def camera_id(self) -> str:
        """Identifier of the camera source."""
        ...

    @property
    def sequence_number(self) -> int:
        """Monotonic sequence number of the tracked frame."""
        ...

    @property
    def timestamp_ns(self) -> int:
        """Monotonic timestamp of the tracked frame in nanoseconds."""
        ...


@runtime_checkable
class ObjectDetector(Protocol):
    """Protocol for framework-independent object detection engines.

    An object detector processes a single captured camera Frame and produces
    a validated DetectionResult containing bounding boxes and class labels.

    Concurrency:
        Implementations are not required to be thread-safe by default. Thread-safety
        and execution concurrency guarantees belong to the concrete adapter or pipeline
        coordinator (e.g., via locks or dedicated worker threads).

    Error Handling:
        Inference or hardware errors must not be silently swallowed or converted into
        an empty successful detection result. The implementation must return a
        DetectionResult with a populated `error` field detailing the failure, or
        raise PerceptionError if the error is unrecoverable.
    """

    def detect(self, frame: Frame) -> DetectionResult:
        """Execute object detection inference on an ingested frame.

        Args:
            frame: A validated camera Frame from the ingestion subsystem.

        Returns:
            DetectionResult: Validated result containing detections, latency,
                             and optional structured failure details.

        Raises:
            PerceptionError: If an unrecoverable pipeline failure occurs.
        """
        ...


@runtime_checkable
class MultiObjectTracker(Protocol):
    """Protocol for framework-independent multi-object tracking engines.

    A tracker maintains persistent object identities across consecutive frames for
    a specific camera stream.

    Lifecycle & State Isolation:
        Each camera feed must be managed by an independent tracker instance to avoid
        cross-camera identity collision. Trackers maintain internal temporal state
        (e.g., motion estimation vectors, lost track age) and expect frames in strictly
        forward chronological order.

    Error Handling:
        Out-of-order frames (sequence_number <= last_sequence_number) or mismatched
        camera IDs must be explicitly rejected to prevent corruption of the motion model.
    """

    def update(self, detection_result: DetectionResult) -> TrackingResultProtocol:
        """Associate detections with active tracks and update spatial-temporal state.

        Args:
            detection_result: Validated detection observations for a camera frame.

        Returns:
            TrackingResultProtocol: Active and updated object tracks for this frame.

        Raises:
            PerceptionError: If an unrecoverable tracking error or out-of-order
                             frame sequence is detected.
        """
        ...

    def reset(self) -> None:
        """Reset internal tracking state and purge active tracks."""
        ...
