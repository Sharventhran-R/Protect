"""Local video file frame source for simulated recorded video playback."""

import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from home_guard.camera.models import (
    CameraConfig,
    Frame,
    FrameMetadata,
    MediaFileError,
    PixelFormat,
    VideoDecoderUnavailableError,
)

# Optional OpenCV import guard
try:
    import cv2

    _OPENCV_AVAILABLE = True
except ImportError:
    _OPENCV_AVAILABLE = False


class FileCameraSource:
    """Consumes and decodes frames from a local video file (MP4/AVI) for simulation replay."""

    def __init__(self, config: CameraConfig, loop: bool = True) -> None:
        """Initialize local file camera source.

        Args:
            config: Camera configuration with valid file_path.
            loop: Whether to loop the video upon reaching EOF.

        Raises:
            VideoDecoderUnavailableError: If opencv-python is not installed.
            MediaFileError: If file_path is missing or not a file.
        """
        if not _OPENCV_AVAILABLE:
            raise VideoDecoderUnavailableError(
                "OpenCV ('opencv-python') is required to decode local video files."
            )

        if config.file_path is None:
            raise MediaFileError(
                "file_path must be specified in CameraConfig for FileCameraSource."
            )

        self._path = Path(config.file_path)
        if not self._path.exists() or not self._path.is_file():
            raise MediaFileError(f"Video file does not exist or is not a file: {self._path}")
        if self._path.stat().st_size == 0:
            raise MediaFileError(f"Video file is empty (0 bytes): {self._path}")

        self._config = config
        self._camera_id = config.camera_id
        self._loop = loop
        self._sequence_number = 0
        self._is_running = False
        self._lock = threading.RLock()

        self._cap: Any = None
        self._base_time_utc = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        self._ns_per_frame = int(1_000_000_000 / self._config.fps)

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
        """Open video capture stream and start the file camera source."""
        with self._lock:
            if self._is_running and self._cap is not None:
                return

            self._cap = cv2.VideoCapture(str(self._path))
            if not self._cap.isOpened():
                self._cap.release()
                self._cap = None
                raise MediaFileError(f"Failed to open video file for decoding: {self._path}")

            self._is_running = True

    def _stop_locked(self) -> None:
        """Internal helper to stop playback and release decoder while holding lock."""
        self._is_running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def stop(self) -> None:
        """Stop playback and release video decoder resources."""
        with self._lock:
            self._stop_locked()

    def capture_frame(self) -> Frame | None:
        """Decode and capture the next frame from the video stream.

        Returns:
            Frame: Decoded and converted frame matching config dimensions and pixel format.
            None: If the source is stopped or reached EOF without looping.
        """
        with self._lock:
            if not self._is_running or self._cap is None:
                return None

            success, raw_frame = self._cap.read()
            if not success:
                if self._loop:
                    # Rewind to frame 0
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    success, raw_frame = self._cap.read()
                    if not success:
                        self._stop_locked()
                        return None
                else:
                    self._stop_locked()
                    return None

            seq = self._sequence_number
            self._sequence_number += 1

            # Resize if dimensions differ from config
            target_h, target_w = self._config.height, self._config.width
            if raw_frame.shape[0] != target_h or raw_frame.shape[1] != target_w:
                raw_frame = cv2.resize(
                    raw_frame, (target_w, target_h), interpolation=cv2.INTER_AREA
                )

            # Convert BGR (cv2 default) to requested format
            if self._config.pixel_format == PixelFormat.RGB24:
                payload = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
            elif self._config.pixel_format == PixelFormat.GRAY8:
                payload = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY)
            else:
                payload = raw_frame

            frame_offset_ns = seq * self._ns_per_frame
            timestamp_ns = 1_767_268_800_000_000_000 + frame_offset_ns
            frame_time = self._base_time_utc + timedelta(microseconds=frame_offset_ns // 1000)

            metadata = FrameMetadata(
                camera_id=self._camera_id,
                sequence_number=seq,
                timestamp_ns=timestamp_ns,
                timestamp_utc=frame_time.isoformat(),
                width=target_w,
                height=target_h,
                pixel_format=self._config.pixel_format,
                scene_label=f"recorded_{self._path.stem}",
            )

            return Frame(metadata=metadata, payload=payload)

    def __enter__(self) -> "FileCameraSource":
        """Context manager support."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit releasing resources."""
        self.stop()
