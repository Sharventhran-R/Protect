"""Camera registry, lifecycle manager, and downstream ingestion coordinator."""

import threading
from typing import Any

from home_guard.camera.buffer import FrameBuffer
from home_guard.camera.metrics import CameraMetrics
from home_guard.camera.models import (
    CameraNotFoundError,
    CameraNotRunningError,
    DuplicateCameraError,
    Frame,
    InvalidFrameError,
    OverflowPolicy,
)
from home_guard.camera.protocols import CameraSource


class CameraManager:
    """Coordinates camera sources, bounded frame buffers, and downstream consumer interfaces."""

    def __init__(self) -> None:
        """Initialize an empty camera manager registry."""
        self._sources: dict[str, CameraSource] = {}
        self._buffers: dict[str, FrameBuffer] = {}
        self._metrics: dict[str, CameraMetrics] = {}
        self._lock = threading.Lock()

    def register_source(
        self,
        source: CameraSource,
        buffer_capacity: int = 30,
        overflow_policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> None:
        """Register a new camera source and allocate a bounded buffer and telemetry tracker.

        Args:
            source: An instance conforming to the CameraSource protocol.
            buffer_capacity: Max queued frames for this camera.
            overflow_policy: Strategy when the buffer reaches capacity.

        Raises:
            DuplicateCameraError: If a camera with the same camera_id already exists.
        """
        camera_id = source.camera_id
        with self._lock:
            if camera_id in self._sources:
                raise DuplicateCameraError(
                    f"A camera source with id '{camera_id}' is already registered."
                )

            self._sources[camera_id] = source
            self._buffers[camera_id] = FrameBuffer(
                capacity=buffer_capacity,
                overflow_policy=overflow_policy,
            )
            self._metrics[camera_id] = CameraMetrics(camera_id)

    def unregister_source(self, camera_id: str) -> None:
        """Stop and remove a camera source and its resources from the registry.

        Args:
            camera_id: Identifier of the camera to remove.

        Raises:
            CameraNotFoundError: If camera_id is not registered.
        """
        with self._lock:
            if camera_id not in self._sources:
                raise CameraNotFoundError(f"Camera '{camera_id}' not found in registry.")

            source = self._sources.pop(camera_id)
            buffer = self._buffers.pop(camera_id)
            self._metrics.pop(camera_id)

        source.stop()
        buffer.clear()

    def get_source(self, camera_id: str) -> CameraSource:
        """Retrieve a registered camera source.

        Args:
            camera_id: Identifier of the desired camera.

        Returns:
            CameraSource: The registered source instance.
        """
        with self._lock:
            if camera_id not in self._sources:
                raise CameraNotFoundError(f"Camera '{camera_id}' not found in registry.")
            return self._sources[camera_id]

    def get_buffer(self, camera_id: str) -> FrameBuffer:
        """Retrieve the bounded buffer assigned to a camera.

        Args:
            camera_id: Identifier of the camera.

        Returns:
            FrameBuffer: Associated buffer instance.
        """
        with self._lock:
            if camera_id not in self._buffers:
                raise CameraNotFoundError(f"Camera '{camera_id}' not found in registry.")
            return self._buffers[camera_id]

    def get_metrics(self, camera_id: str) -> CameraMetrics:
        """Retrieve telemetry tracker for a camera.

        Args:
            camera_id: Identifier of the camera.

        Returns:
            CameraMetrics: Associated metrics instance.
        """
        with self._lock:
            if camera_id not in self._metrics:
                raise CameraNotFoundError(f"Camera '{camera_id}' not found in registry.")
            return self._metrics[camera_id]

    def get_telemetry_snapshot(self, camera_id: str) -> dict[str, Any]:
        """Get structured metrics snapshot including current buffer occupancy.

        Args:
            camera_id: Identifier of the camera.

        Returns:
            dict[str, Any]: Metrics snapshot dictionary.
        """
        with self._lock:
            if camera_id not in self._metrics:
                raise CameraNotFoundError(f"Camera '{camera_id}' not found in registry.")
            metrics = self._metrics[camera_id]
            buffer = self._buffers[camera_id]

        return metrics.snapshot(current_occupancy=buffer.occupancy)

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """Retrieve metrics snapshots for all registered cameras."""
        with self._lock:
            camera_ids = list(self._sources.keys())

        return {cam_id: self.get_telemetry_snapshot(cam_id) for cam_id in camera_ids}

    def start_camera(self, camera_id: str) -> None:
        """Start an individual registered camera source."""
        source = self.get_source(camera_id)
        source.start()

    def stop_camera(self, camera_id: str) -> None:
        """Stop an individual registered camera source."""
        source = self.get_source(camera_id)
        source.stop()

    def start_all(self) -> None:
        """Start all registered camera sources."""
        with self._lock:
            sources = list(self._sources.values())
        for source in sources:
            source.start()

    def stop_all(self) -> None:
        """Stop all registered camera sources."""
        with self._lock:
            sources = list(self._sources.values())
        for source in sources:
            source.stop()

    def ingest_next_frame(self, camera_id: str) -> Frame | None:
        """Capture one frame from the source and queue it into the camera's bounded buffer.

        Args:
            camera_id: Target camera identifier.

        Returns:
            Frame: Captured and enqueued frame, or None if source has stopped or reached EOF.

        Raises:
            CameraNotRunningError: If the requested camera is not active.
            InvalidFrameError: If frame data is corrupted or violates schema.
        """
        source = self.get_source(camera_id)
        buffer = self.get_buffer(camera_id)
        metrics = self.get_metrics(camera_id)

        if not source.is_running:
            raise CameraNotRunningError(
                f"Cannot ingest from inactive camera '{camera_id}'. Call start() first."
            )

        try:
            frame = source.capture_frame()
        except Exception:
            metrics.record_error()
            raise

        if frame is None:
            return None

        # Verify frame matches camera_id
        if frame.metadata.camera_id != camera_id:
            metrics.record_invalid()
            raise InvalidFrameError(
                f"Frame camera_id '{frame.metadata.camera_id}' does not match "
                f"source id '{camera_id}'."
            )

        metrics.record_produced(
            sequence_number=frame.metadata.sequence_number,
            timestamp_utc=frame.metadata.timestamp_utc,
        )

        accepted = buffer.push(frame)
        if not accepted:
            metrics.record_dropped()

        return frame

    def get_next_frame(self, camera_id: str, timeout: float | None = None) -> Frame | None:
        """Downstream consumer interface: Pop the next frame from the camera buffer.

        This is the primary public contract for Phase 2 (Object Detection & Tracking)
        to consume frames from Phase 1 without coupling to internal generators.

        Args:
            camera_id: Target camera identifier.
            timeout: Optional seconds to wait if buffer is empty.

        Returns:
            Frame: Oldest available Frame object, or None if buffer is empty.
        """
        buffer = self.get_buffer(camera_id)
        metrics = self.get_metrics(camera_id)

        frame = buffer.pop(timeout=timeout)
        if frame is not None:
            metrics.record_consumed()

        return frame

    def shutdown(self) -> None:
        """Stop all sources and flush all buffers cleanly."""
        self.stop_all()
        with self._lock:
            for buf in self._buffers.values():
                buf.clear()
            self._sources.clear()
            self._buffers.clear()
            self._metrics.clear()
