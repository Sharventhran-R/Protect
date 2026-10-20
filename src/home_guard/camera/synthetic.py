"""Deterministic, CPU-only synthetic camera frame generator."""

import threading
from datetime import UTC, datetime, timedelta
from typing import cast

import numpy as np
from numpy.typing import NDArray

from home_guard.camera.models import (
    CameraConfig,
    Frame,
    FrameMetadata,
    PixelFormat,
)


class SyntheticCameraSource:
    """Generates deterministic synthetic optical frames without physical cameras or GPUs."""

    def __init__(self, config: CameraConfig) -> None:
        """Initialize synthetic camera source with validated configuration.

        Args:
            config: Camera configuration defining dimensions, fps, seed, and camera_id.
        """
        self._config = config
        self._camera_id = config.camera_id
        self._width = config.width
        self._height = config.height
        self._fps = config.fps
        self._pixel_format = config.pixel_format
        self._seed = config.seed if config.seed is not None else hash(self._camera_id) & 0x7FFFFFFF

        self._sequence_number = 0
        self._is_running = False
        self._lock = threading.Lock()

        # Deterministic base timestamp (Fixed reference epoch for reproducible time progression)
        self._base_time_utc = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        self._ns_per_frame = int(1_000_000_000 / self._fps)

        # Pre-generate base background using deterministic RNG
        rng = np.random.default_rng(self._seed)
        self._base_color = rng.integers(30, 180, size=(3,), dtype=np.uint8)
        self._accent_color = rng.integers(180, 255, size=(3,), dtype=np.uint8)

    @property
    def camera_id(self) -> str:
        """Unique identifier of the camera source."""
        return self._camera_id

    @property
    def config(self) -> CameraConfig:
        """Immutable configuration object for this source."""
        return self._config

    @property
    def is_running(self) -> bool:
        """Current operational state of the camera source."""
        return self._is_running

    def start(self) -> None:
        """Start the synthetic camera source."""
        with self._lock:
            self._is_running = True

    def stop(self) -> None:
        """Stop the synthetic camera source."""
        with self._lock:
            self._is_running = False

    def reset(self) -> None:
        """Reset sequence number and deterministic state."""
        with self._lock:
            self._sequence_number = 0

    def capture_frame(self) -> Frame | None:
        """Generate and capture the next deterministic synthetic frame.

        Returns:
            Frame: The synthesized frame combining metadata and rendered payload.
            None: If the source is stopped.
        """
        with self._lock:
            if not self._is_running:
                return None

            seq = self._sequence_number
            self._sequence_number += 1

            # Deterministic timestamps
            frame_offset_ns = seq * self._ns_per_frame
            timestamp_ns = 1_767_268_800_000_000_000 + frame_offset_ns
            frame_time = self._base_time_utc + timedelta(microseconds=frame_offset_ns // 1000)
            timestamp_utc = frame_time.isoformat()

            # Generate synthetic image payload
            payload = self._render_synthetic_payload(seq)

            metadata = FrameMetadata(
                camera_id=self._camera_id,
                sequence_number=seq,
                timestamp_ns=timestamp_ns,
                timestamp_utc=timestamp_utc,
                width=self._width,
                height=self._height,
                pixel_format=self._pixel_format,
                scene_label=f"simulated_{self._config.location_name}",
            )

            return Frame(metadata=metadata, payload=payload)

    def _render_synthetic_payload(self, seq: int) -> NDArray[np.uint8]:
        """Render a deterministic synthetic scene payload with moving shapes.

        Args:
            seq: The current frame sequence number.

        Returns:
            np.ndarray: Formatted pixel array matching target dimensions and format.
        """
        # Create base background gradient
        img = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        img[:, :] = self._base_color

        # Subtle gradient along rows
        row_gradient = (np.linspace(0, 40, self._height, dtype=np.uint8))[:, None, None]
        img = np.clip(img.astype(np.int16) + row_gradient, 0, 255).astype(np.uint8)

        # Draw simulated moving objects (e.g. simulated pedestrian/vehicle box)
        # Position translates smoothly across frame based on sequence number
        obj_w, obj_h = max(16, self._width // 8), max(16, self._height // 8)
        max_x = max(1, self._width - obj_w)
        max_y = max(1, self._height - obj_h)

        x_pos = (seq * 8) % max_x
        y_pos = (seq * 4) % max_y

        img[y_pos : y_pos + obj_h, x_pos : x_pos + obj_w] = self._accent_color

        # Draw a second stationary object (e.g., simulated delivery package)
        pkg_x = self._width // 2
        pkg_y = (self._height * 3) // 4
        pkg_size = min(24, self._width // 16, self._height // 16)
        if pkg_x + pkg_size <= self._width and pkg_y + pkg_size <= self._height:
            img[pkg_y : pkg_y + pkg_size, pkg_x : pkg_x + pkg_size] = (210, 140, 40)

        # Draw binary sequence indicator pattern in top-left corner (16x16 block)
        indicator_size = min(16, self._width, self._height)
        val = seq % 256
        img[0:indicator_size, 0:indicator_size] = (val, 255 - val, (val * 2) % 255)

        # Convert to requested pixel format
        if self._pixel_format == PixelFormat.GRAY8:
            # Grayscale: 0.299 R + 0.587 G + 0.114 B
            gray = (0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]).astype(
                np.uint8
            )
            return cast(NDArray[np.uint8], gray)
        elif self._pixel_format == PixelFormat.BGR24:
            # BGR: swap channels 0 and 2
            bgr = img.copy()
            bgr[:, :, 0] = img[:, :, 2]
            bgr[:, :, 2] = img[:, :, 0]
            return cast(NDArray[np.uint8], bgr)

        # Default RGB24
        return cast(NDArray[np.uint8], img)
