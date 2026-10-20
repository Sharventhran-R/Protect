"""Lightweight, thread-safe ingestion metrics and telemetry."""

import threading
from typing import Any


class CameraMetrics:
    """Thread-safe statistics counter for camera frames and buffer telemetry."""

    def __init__(self, camera_id: str) -> None:
        """Initialize telemetry counters for a single camera.

        Args:
            camera_id: Identifier of the camera being observed.
        """
        self._camera_id = camera_id
        self._frames_produced = 0
        self._frames_consumed = 0
        self._frames_dropped = 0
        self._invalid_frames = 0
        self._source_errors = 0
        self._last_sequence_number = -1
        self._last_capture_timestamp_utc: str | None = None
        self._lock = threading.Lock()

    @property
    def camera_id(self) -> str:
        """Camera identifier for this metrics instance."""
        return self._camera_id

    @property
    def frames_produced(self) -> int:
        """Total number of frames successfully generated or captured."""
        with self._lock:
            return self._frames_produced

    @property
    def frames_consumed(self) -> int:
        """Total number of frames consumed downstream."""
        with self._lock:
            return self._frames_consumed

    @property
    def frames_dropped(self) -> int:
        """Total number of frames dropped due to buffer overflow."""
        with self._lock:
            return self._frames_dropped

    @property
    def invalid_frames(self) -> int:
        """Total number of malformed frames rejected during ingestion."""
        with self._lock:
            return self._invalid_frames

    @property
    def source_errors(self) -> int:
        """Total number of source-level exceptions or failures recorded."""
        with self._lock:
            return self._source_errors

    def record_produced(self, sequence_number: int, timestamp_utc: str) -> None:
        """Record a newly captured frame."""
        with self._lock:
            self._frames_produced += 1
            self._last_sequence_number = sequence_number
            self._last_capture_timestamp_utc = timestamp_utc

    def record_consumed(self) -> None:
        """Record downstream consumption of a frame."""
        with self._lock:
            self._frames_consumed += 1

    def record_dropped(self) -> None:
        """Record a frame dropped due to buffer overflow."""
        with self._lock:
            self._frames_dropped += 1

    def record_invalid(self) -> None:
        """Record an invalid frame encountered during ingestion."""
        with self._lock:
            self._invalid_frames += 1

    def record_error(self) -> None:
        """Record a source exception or operational failure."""
        with self._lock:
            self._source_errors += 1

    def snapshot(self, current_occupancy: int = 0) -> dict[str, Any]:
        """Generate an immutable telemetry snapshot dictionary.

        Args:
            current_occupancy: Current queue depth of the corresponding buffer.

        Returns:
            dict[str, Any]: Structured metrics summary.
        """
        with self._lock:
            return {
                "camera_id": self._camera_id,
                "frames_produced": self._frames_produced,
                "frames_consumed": self._frames_consumed,
                "frames_dropped": self._frames_dropped,
                "invalid_frames": self._invalid_frames,
                "source_errors": self._source_errors,
                "current_occupancy": current_occupancy,
                "last_sequence_number": self._last_sequence_number,
                "last_capture_timestamp_utc": self._last_capture_timestamp_utc,
            }
