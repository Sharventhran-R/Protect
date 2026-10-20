"""Unit and integration tests for Phase 1 camera subsystem."""

import threading
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from home_guard.camera import (
    CameraConfig,
    CameraManager,
    CameraMetrics,
    CameraNotFoundError,
    CameraNotRunningError,
    DuplicateCameraError,
    FileCameraSource,
    Frame,
    FrameBuffer,
    FrameMetadata,
    InvalidCameraConfigError,
    InvalidFrameError,
    MediaFileError,
    OverflowPolicy,
    PixelFormat,
    SourceType,
    SyntheticCameraSource,
)

# --- 1. Camera Configuration Tests ---


def test_valid_camera_config() -> None:
    """Verify that a valid CameraConfig initializes successfully."""
    config = CameraConfig(
        camera_id="front_porch",
        source_type=SourceType.SYNTHETIC,
        width=1280,
        height=720,
        fps=30.0,
        pixel_format=PixelFormat.RGB24,
        location_name="front_porch",
        seed=101,
    )
    assert config.camera_id == "front_porch"
    assert config.width == 1280
    assert config.height == 720
    assert config.fps == 30.0
    assert config.pixel_format == PixelFormat.RGB24
    assert config.seed == 101


@pytest.mark.parametrize(
    "camera_id, width, height, fps, file_path, source_type",
    [
        ("", 640, 480, 30.0, None, SourceType.SYNTHETIC),  # Empty id
        ("cam invalid spaces", 640, 480, 30.0, None, SourceType.SYNTHETIC),  # Invalid chars
        ("cam1", 0, 480, 30.0, None, SourceType.SYNTHETIC),  # Width 0
        ("cam1", -10, 480, 30.0, None, SourceType.SYNTHETIC),  # Negative width
        ("cam1", 640, 0, 30.0, None, SourceType.SYNTHETIC),  # Height 0
        ("cam1", 640, -5, 30.0, None, SourceType.SYNTHETIC),  # Negative height
        ("cam1", 640, 480, 0.0, None, SourceType.SYNTHETIC),  # FPS 0
        ("cam1", 640, 480, -10.0, None, SourceType.SYNTHETIC),  # Negative FPS
        ("cam1", 640, 480, 300.0, None, SourceType.SYNTHETIC),  # Excessive FPS (>240)
        ("cam1", 640, 480, 30.0, None, SourceType.FILE),  # FILE source without file_path
    ],
)
def test_invalid_camera_config_raises(
    camera_id: str,
    width: int,
    height: int,
    fps: float,
    file_path: Path | None,
    source_type: SourceType,
) -> None:
    """Verify that invalid configurations raise InvalidCameraConfigError."""
    with pytest.raises(InvalidCameraConfigError):
        CameraConfig(
            camera_id=camera_id,
            source_type=source_type,
            width=width,
            height=height,
            fps=fps,
            file_path=file_path,
        )


# --- 2. Frame Metadata and Payload Validation ---


def test_valid_frame_creation() -> None:
    """Verify that a valid Frame and FrameMetadata combine successfully."""
    meta = FrameMetadata(
        camera_id="cam_01",
        sequence_number=0,
        timestamp_ns=1700000000000000000,
        timestamp_utc="2026-01-01T12:00:00+00:00",
        width=320,
        height=240,
        pixel_format=PixelFormat.RGB24,
    )
    payload = np.zeros((240, 320, 3), dtype=np.uint8)
    frame = Frame(metadata=meta, payload=payload)

    assert frame.metadata.camera_id == "cam_01"
    assert frame.metadata.sequence_number == 0
    assert len(frame.to_bytes()) == 240 * 320 * 3

    # Verify __repr__ does not dump raw pixel arrays
    repr_str = repr(frame)
    assert "cam_01" in repr_str
    assert "shape=(240, 320, 3)" in repr_str
    assert "[[[" not in repr_str  # No raw array dump


def test_invalid_frame_metadata_raises() -> None:
    """Verify that malformed metadata parameters are rejected."""
    # Negative sequence number
    with pytest.raises(InvalidFrameError):
        FrameMetadata(
            camera_id="cam1",
            sequence_number=-1,
            timestamp_ns=1000,
            timestamp_utc="2026-01-01T12:00:00+00:00",
            width=100,
            height=100,
            pixel_format=PixelFormat.RGB24,
        )

    # Invalid timestamp
    with pytest.raises(InvalidFrameError):
        FrameMetadata(
            camera_id="cam1",
            sequence_number=0,
            timestamp_ns=1000,
            timestamp_utc="not_a_valid_timestamp",
            width=100,
            height=100,
            pixel_format=PixelFormat.RGB24,
        )


def test_frame_payload_shape_and_dtype_mismatch_raises() -> None:
    """Verify that payload shape or dtype mismatches raise InvalidFrameError."""
    meta = FrameMetadata(
        camera_id="cam1",
        sequence_number=0,
        timestamp_ns=1000,
        timestamp_utc="2026-01-01T12:00:00+00:00",
        width=100,
        height=100,
        pixel_format=PixelFormat.RGB24,
    )

    # Wrong shape
    wrong_shape = np.zeros((50, 50, 3), dtype=np.uint8)
    with pytest.raises(InvalidFrameError):
        Frame(metadata=meta, payload=wrong_shape)

    # Wrong dtype (float32 instead of uint8)
    wrong_dtype = np.zeros((100, 100, 3), dtype=np.float32)
    with pytest.raises(InvalidFrameError):
        Frame(metadata=meta, payload=wrong_dtype)

    # Wrong dimensions for GRAY8
    meta_gray = FrameMetadata(
        camera_id="cam1",
        sequence_number=0,
        timestamp_ns=1000,
        timestamp_utc="2026-01-01T12:00:00+00:00",
        width=100,
        height=100,
        pixel_format=PixelFormat.GRAY8,
    )
    with pytest.raises(InvalidFrameError):
        Frame(metadata=meta_gray, payload=np.zeros((100, 100, 3), dtype=np.uint8))


# --- 3. Deterministic Synthetic Camera Source ---


def test_synthetic_camera_reproducibility() -> None:
    """Verify that identical configurations and seeds yield byte-for-byte identical frames."""
    cfg1 = CameraConfig(camera_id="cam_sim", width=160, height=120, fps=10.0, seed=42)
    cfg2 = CameraConfig(camera_id="cam_sim", width=160, height=120, fps=10.0, seed=42)

    src1 = SyntheticCameraSource(cfg1)
    src2 = SyntheticCameraSource(cfg2)

    src1.start()
    src2.start()

    for _ in range(5):
        f1 = src1.capture_frame()
        f2 = src2.capture_frame()
        assert f1 is not None and f2 is not None
        assert f1.metadata.sequence_number == f2.metadata.sequence_number
        assert f1.metadata.timestamp_ns == f2.metadata.timestamp_ns
        assert np.array_equal(f1.payload, f2.payload)

    src1.stop()
    src2.stop()


def test_synthetic_camera_different_seeds_produce_variation() -> None:
    """Verify that different seeds produce visually distinct frames."""
    cfg1 = CameraConfig(camera_id="cam_1", width=160, height=120, seed=1)
    cfg2 = CameraConfig(camera_id="cam_2", width=160, height=120, seed=999)

    src1 = SyntheticCameraSource(cfg1)
    src2 = SyntheticCameraSource(cfg2)

    src1.start()
    src2.start()

    f1 = src1.capture_frame()
    f2 = src2.capture_frame()

    assert f1 is not None and f2 is not None
    assert not np.array_equal(f1.payload, f2.payload)

    src1.stop()
    src2.stop()


def test_synthetic_camera_sequence_monotonicity() -> None:
    """Verify sequence numbers strictly increment by 1 on each capture."""
    cfg = CameraConfig(camera_id="cam_seq", width=80, height=60, fps=10.0, seed=10)
    src = SyntheticCameraSource(cfg)
    src.start()

    for expected_seq in range(10):
        frame = src.capture_frame()
        assert frame is not None
        assert frame.metadata.sequence_number == expected_seq

    src.stop()
    assert src.capture_frame() is None


# --- 4. Bounded Buffer and Overflow Policy ---


def test_buffer_bounded_capacity() -> None:
    """Verify buffer enforces maximum capacity."""
    buf = FrameBuffer(capacity=3, overflow_policy=OverflowPolicy.DROP_OLDEST)
    assert buf.capacity == 3
    assert buf.occupancy == 0
    assert buf.is_empty is True
    assert buf.is_full is False


def test_buffer_overflow_drop_oldest() -> None:
    """Verify DROP_OLDEST discards the oldest item when capacity is exceeded."""
    buf = FrameBuffer(capacity=2, overflow_policy=OverflowPolicy.DROP_OLDEST)

    def make_frame(seq: int) -> Frame:
        meta = FrameMetadata(
            camera_id="cam",
            sequence_number=seq,
            timestamp_ns=1000 + seq,
            timestamp_utc="2026-01-01T12:00:00+00:00",
            width=64,
            height=64,
            pixel_format=PixelFormat.GRAY8,
        )
        return Frame(metadata=meta, payload=np.zeros((64, 64), dtype=np.uint8))

    assert buf.push(make_frame(0)) is True  # Occupancy 1
    assert buf.push(make_frame(1)) is True  # Occupancy 2 (full)
    assert buf.is_full is True

    # Pushing frame 2 triggers DROP_OLDEST (frame 0 dropped)
    assert buf.push(make_frame(2)) is False
    assert buf.occupancy == 2

    # Popping should yield frame 1 then frame 2
    f1 = buf.pop()
    assert f1 is not None and f1.metadata.sequence_number == 1
    f2 = buf.pop()
    assert f2 is not None and f2.metadata.sequence_number == 2
    assert buf.pop() is None


def test_buffer_overflow_reject_newest() -> None:
    """Verify REJECT_NEWEST discards incoming frames when full."""
    buf = FrameBuffer(capacity=2, overflow_policy=OverflowPolicy.REJECT_NEWEST)

    def make_frame(seq: int) -> Frame:
        meta = FrameMetadata(
            camera_id="cam",
            sequence_number=seq,
            timestamp_ns=1000 + seq,
            timestamp_utc="2026-01-01T12:00:00+00:00",
            width=64,
            height=64,
            pixel_format=PixelFormat.GRAY8,
        )
        return Frame(metadata=meta, payload=np.zeros((64, 64), dtype=np.uint8))

    assert buf.push(make_frame(0)) is True
    assert buf.push(make_frame(1)) is True

    # Frame 2 is rejected
    assert buf.push(make_frame(2)) is False

    # Popped frames remain frame 0 and frame 1
    f0 = buf.pop()
    assert f0 is not None and f0.metadata.sequence_number == 0
    f1 = buf.pop()
    assert f1 is not None and f1.metadata.sequence_number == 1
    assert buf.pop() is None


# --- 5. Telemetry & Metrics ---


def test_camera_metrics_tracking() -> None:
    """Verify telemetry counters track production, consumption, and drops accurately."""
    metrics = CameraMetrics("driveway")
    assert metrics.camera_id == "driveway"
    assert metrics.frames_produced == 0

    metrics.record_produced(sequence_number=0, timestamp_utc="2026-01-01T12:00:00+00:00")
    metrics.record_produced(sequence_number=1, timestamp_utc="2026-01-01T12:00:01+00:00")
    metrics.record_consumed()
    metrics.record_dropped()
    metrics.record_invalid()
    metrics.record_error()

    snap = metrics.snapshot(current_occupancy=1)
    assert snap["camera_id"] == "driveway"
    assert snap["frames_produced"] == 2
    assert snap["frames_consumed"] == 1
    assert snap["frames_dropped"] == 1
    assert snap["invalid_frames"] == 1
    assert snap["source_errors"] == 1
    assert snap["current_occupancy"] == 1
    assert snap["last_sequence_number"] == 1


# --- 6. Camera Manager Lifecycle & Downstream Consumer API ---


def test_manager_registration_and_duplicate_rejection() -> None:
    """Verify duplicate camera identifiers are rejected."""
    mgr = CameraManager()
    cfg = CameraConfig(camera_id="cam_main", width=160, height=120)
    src = SyntheticCameraSource(cfg)

    mgr.register_source(src)
    assert mgr.get_source("cam_main") is src

    # Duplicate registration must fail
    with pytest.raises(DuplicateCameraError):
        mgr.register_source(src)

    mgr.shutdown()


def test_manager_multi_camera_isolation() -> None:
    """Verify independent cameras operate in total isolation."""
    mgr = CameraManager()
    src_a = SyntheticCameraSource(CameraConfig(camera_id="cam_a", width=80, height=60, seed=1))
    src_b = SyntheticCameraSource(CameraConfig(camera_id="cam_b", width=80, height=60, seed=2))

    mgr.register_source(src_a, buffer_capacity=5)
    mgr.register_source(src_b, buffer_capacity=5)

    mgr.start_all()

    # Ingest 3 frames on A, 1 frame on B
    mgr.ingest_next_frame("cam_a")
    mgr.ingest_next_frame("cam_a")
    mgr.ingest_next_frame("cam_a")
    mgr.ingest_next_frame("cam_b")

    snap_a = mgr.get_telemetry_snapshot("cam_a")
    snap_b = mgr.get_telemetry_snapshot("cam_b")

    assert snap_a["frames_produced"] == 3
    assert snap_a["current_occupancy"] == 3

    assert snap_b["frames_produced"] == 1
    assert snap_b["current_occupancy"] == 1

    # Downstream consumption on A leaves B unchanged
    frame_a = mgr.get_next_frame("cam_a")
    assert frame_a is not None and frame_a.metadata.camera_id == "cam_a"
    assert mgr.get_telemetry_snapshot("cam_a")["current_occupancy"] == 2
    assert mgr.get_telemetry_snapshot("cam_b")["current_occupancy"] == 1

    mgr.shutdown()


def test_manager_ingest_from_inactive_camera_raises() -> None:
    """Verify ingest_next_frame raises CameraNotRunningError if not started."""
    mgr = CameraManager()
    src = SyntheticCameraSource(CameraConfig(camera_id="cam_off", width=80, height=60))
    mgr.register_source(src)

    with pytest.raises(CameraNotRunningError):
        mgr.ingest_next_frame("cam_off")

    mgr.shutdown()


def test_manager_unknown_camera_queries_raise() -> None:
    """Verify querying unregistered cameras raises CameraNotFoundError."""
    mgr = CameraManager()
    with pytest.raises(CameraNotFoundError):
        mgr.get_source("ghost_cam")

    with pytest.raises(CameraNotFoundError):
        mgr.get_next_frame("ghost_cam")


# --- 7. FileCameraSource Integration Tests ---


def test_file_source_missing_file_raises(tmp_path: Path) -> None:
    """Verify FileCameraSource raises MediaFileError when the file does not exist."""
    missing = tmp_path / "does_not_exist.mp4"
    cfg = CameraConfig(
        camera_id="cam_file",
        source_type=SourceType.FILE,
        file_path=missing,
    )
    with pytest.raises(MediaFileError):
        FileCameraSource(cfg)


def test_file_source_playback_and_looping(tmp_path: Path) -> None:
    """Verify FileCameraSource decodes frames, resizes, and loops smoothly."""
    video_path = tmp_path / "test_sim.avi"
    width, height, fps = 160, 120, 10

    # Synthesize a tiny 3-frame test video file using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # type: ignore[attr-defined]
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    for i in range(3):
        frame_data = np.full((height, width, 3), i * 50, dtype=np.uint8)
        out.write(frame_data)
    out.release()

    cfg = CameraConfig(
        camera_id="recorded_cam",
        source_type=SourceType.FILE,
        width=width,
        height=height,
        fps=float(fps),
        file_path=video_path,
        pixel_format=PixelFormat.RGB24,
    )

    with FileCameraSource(cfg, loop=True) as src:
        assert src.is_running is True

        # Read 7 frames (proves looping over 3-frame video)
        for expected_seq in range(7):
            frame = src.capture_frame()
            assert frame is not None
            assert frame.metadata.sequence_number == expected_seq
            assert frame.metadata.camera_id == "recorded_cam"
            assert frame.payload.shape == (height, width, 3)

    assert src.is_running is False


# --- 8. Robustness, Concurrency & Extended Verification Tests ---


def test_buffer_concurrent_producers_and_consumers() -> None:
    """Verify thread safety with concurrent producers and consumers under bounded capacity."""
    capacity = 10
    buf = FrameBuffer(capacity=capacity, overflow_policy=OverflowPolicy.DROP_OLDEST)
    num_producers = 3
    frames_per_producer = 40
    consumed_frames: list[Frame] = []
    consumed_lock = threading.Lock()
    errors: list[Exception] = []

    def producer_worker(prod_id: int) -> None:
        try:
            for seq in range(frames_per_producer):
                meta = FrameMetadata(
                    camera_id=f"prod_{prod_id}",
                    sequence_number=seq,
                    timestamp_ns=1000 + seq,
                    timestamp_utc="2026-01-01T12:00:00+00:00",
                    width=64,
                    height=64,
                    pixel_format=PixelFormat.GRAY8,
                )
                frame = Frame(metadata=meta, payload=np.zeros((64, 64), dtype=np.uint8))
                buf.push(frame)
        except Exception as exc:
            errors.append(exc)

    stop_consumer = threading.Event()

    def consumer_worker() -> None:
        try:
            while not stop_consumer.is_set() or not buf.is_empty:
                frame = buf.pop(timeout=0.01)
                if frame is not None:
                    with consumed_lock:
                        consumed_frames.append(frame)
        except Exception as exc:
            errors.append(exc)

    producers = [threading.Thread(target=producer_worker, args=(i,)) for i in range(num_producers)]
    consumers = [threading.Thread(target=consumer_worker) for _ in range(2)]

    for c in consumers:
        c.start()
    for p in producers:
        p.start()

    for p in producers:
        p.join(timeout=5.0)
        assert not p.is_alive(), "Producer thread timed out"

    stop_consumer.set()

    for c in consumers:
        c.join(timeout=5.0)
        assert not c.is_alive(), "Consumer thread timed out"

    assert not errors, f"Encountered thread errors: {errors}"
    assert 0 <= buf.occupancy <= capacity
    total_produced = num_producers * frames_per_producer
    total_received = len(consumed_frames) + buf.occupancy
    assert total_received <= total_produced
    assert len(consumed_frames) > 0


def test_buffer_timed_pop_monotonic_timeout() -> None:
    """Verify pop with timeout waits for frame or expires cleanly using monotonic clock."""
    buf = FrameBuffer(capacity=5)

    # Empty buffer times out after specified duration
    start = time.monotonic()
    frame = buf.pop(timeout=0.05)
    elapsed = time.monotonic() - start
    assert frame is None
    assert elapsed >= 0.04

    # Pushing unblocks a timed pop
    def delayed_push() -> None:
        time.sleep(0.02)
        meta = FrameMetadata(
            camera_id="cam_timed",
            sequence_number=0,
            timestamp_ns=1000,
            timestamp_utc="2026-01-01T12:00:00+00:00",
            width=64,
            height=64,
            pixel_format=PixelFormat.GRAY8,
        )
        buf.push(Frame(metadata=meta, payload=np.zeros((64, 64), dtype=np.uint8)))

    t = threading.Thread(target=delayed_push)
    t.start()
    f = buf.pop(timeout=1.0)
    t.join(timeout=2.0)

    assert f is not None
    assert f.metadata.camera_id == "cam_timed"


def test_manager_repeated_shutdown_idempotent() -> None:
    """Verify calling CameraManager.shutdown() repeatedly is completely idempotent and safe."""
    mgr = CameraManager()
    src = SyntheticCameraSource(CameraConfig(camera_id="cam_shut", width=80, height=60))
    mgr.register_source(src)
    mgr.start_all()

    # First shutdown stops all cameras and purges registry
    mgr.shutdown()
    assert not src.is_running

    # Successive calls must succeed without error
    mgr.shutdown()
    mgr.shutdown()
    assert mgr.get_all_metrics() == {}


def test_manager_unregister_source_stops_and_cleans_resources() -> None:
    """Verify unregister_source stops the source, flushes its buffer, and removes entries."""
    mgr = CameraManager()
    src = SyntheticCameraSource(CameraConfig(camera_id="cam_unreg", width=80, height=60))
    mgr.register_source(src, buffer_capacity=5)
    mgr.start_camera("cam_unreg")
    mgr.ingest_next_frame("cam_unreg")

    buf = mgr.get_buffer("cam_unreg")
    assert buf.occupancy == 1

    mgr.unregister_source("cam_unreg")

    assert not src.is_running
    assert buf.occupancy == 0

    with pytest.raises(CameraNotFoundError):
        mgr.get_source("cam_unreg")
    with pytest.raises(CameraNotFoundError):
        mgr.get_buffer("cam_unreg")
    with pytest.raises(CameraNotFoundError):
        mgr.get_metrics("cam_unreg")
    with pytest.raises(CameraNotFoundError):
        mgr.unregister_source("cam_unreg")


def test_file_source_non_looping_eof(tmp_path: Path) -> None:
    """Verify FileCameraSource(loop=False) stops and returns None upon reaching video EOF."""
    video_path = tmp_path / "eof_test.avi"
    width, height, fps = 80, 60, 10
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # type: ignore[attr-defined]
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    for i in range(2):
        out.write(np.full((height, width, 3), i * 100, dtype=np.uint8))
    out.release()

    cfg = CameraConfig(
        camera_id="cam_eof",
        source_type=SourceType.FILE,
        width=width,
        height=height,
        fps=float(fps),
        file_path=video_path,
    )
    src = FileCameraSource(cfg, loop=False)
    src.start()

    f0 = src.capture_frame()
    assert f0 is not None and f0.metadata.sequence_number == 0

    f1 = src.capture_frame()
    assert f1 is not None and f1.metadata.sequence_number == 1

    # End of video reached with loop=False -> returns None and source transitions to stopped
    f2 = src.capture_frame()
    assert f2 is None
    assert not src.is_running

    # Subsequent capture while stopped also returns None
    assert src.capture_frame() is None


def test_file_source_empty_and_corrupt_files_raise(tmp_path: Path) -> None:
    """Verify empty and corrupt video files raise MediaFileError."""
    # Case 1: Empty (0-byte) file raises MediaFileError on construction
    empty_file = tmp_path / "empty_video.mp4"
    empty_file.touch()

    cfg_empty = CameraConfig(
        camera_id="cam_empty",
        source_type=SourceType.FILE,
        width=80,
        height=60,
        file_path=empty_file,
    )
    with pytest.raises(MediaFileError):
        FileCameraSource(cfg_empty)

    # Case 2: Corrupt file (non-empty arbitrary bytes) raises MediaFileError on start()
    corrupt_file = tmp_path / "corrupt_video.mp4"
    corrupt_file.write_bytes(b"INVALID_VIDEO_HEADER_AND_GARBAGE_PAYLOAD_BYTES")

    cfg_corrupt = CameraConfig(
        camera_id="cam_corrupt",
        source_type=SourceType.FILE,
        width=80,
        height=60,
        file_path=corrupt_file,
    )
    src = FileCameraSource(cfg_corrupt)
    with pytest.raises(MediaFileError):
        src.start()


def test_synthetic_camera_pixel_formats() -> None:
    """Verify SyntheticCameraSource generates valid payloads for BGR24 and GRAY8 formats."""
    # BGR24
    cfg_bgr = CameraConfig(
        camera_id="cam_bgr",
        width=80,
        height=60,
        fps=10.0,
        pixel_format=PixelFormat.BGR24,
        seed=42,
    )
    src_bgr = SyntheticCameraSource(cfg_bgr)
    src_bgr.start()
    f_bgr = src_bgr.capture_frame()
    assert f_bgr is not None
    assert f_bgr.metadata.pixel_format == PixelFormat.BGR24
    assert f_bgr.payload.shape == (60, 80, 3)
    assert f_bgr.payload.dtype == np.uint8

    # Compare BGR with RGB to verify channel swap
    cfg_rgb = CameraConfig(
        camera_id="cam_rgb",
        width=80,
        height=60,
        fps=10.0,
        pixel_format=PixelFormat.RGB24,
        seed=42,
    )
    src_rgb = SyntheticCameraSource(cfg_rgb)
    src_rgb.start()
    f_rgb = src_rgb.capture_frame()
    assert f_rgb is not None
    # Blue channel of BGR equals Red channel of RGB
    assert np.array_equal(f_bgr.payload[:, :, 0], f_rgb.payload[:, :, 2])
    # Red channel of BGR equals Blue channel of RGB
    assert np.array_equal(f_bgr.payload[:, :, 2], f_rgb.payload[:, :, 0])
    # Green channel is identical
    assert np.array_equal(f_bgr.payload[:, :, 1], f_rgb.payload[:, :, 1])

    # GRAY8
    cfg_gray = CameraConfig(
        camera_id="cam_gray",
        width=80,
        height=60,
        fps=10.0,
        pixel_format=PixelFormat.GRAY8,
        seed=42,
    )
    src_gray = SyntheticCameraSource(cfg_gray)
    src_gray.start()
    f_gray = src_gray.capture_frame()
    assert f_gray is not None
    assert f_gray.metadata.pixel_format == PixelFormat.GRAY8
    assert f_gray.payload.shape == (60, 80)
    assert f_gray.payload.dtype == np.uint8


def test_file_source_pixel_formats(tmp_path: Path) -> None:
    """Verify FileCameraSource converts frames to BGR24 and GRAY8 formats correctly."""
    video_path = tmp_path / "fmt_test.avi"
    width, height, fps = 80, 60, 10
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # type: ignore[attr-defined]
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    test_img = np.zeros((height, width, 3), dtype=np.uint8)
    test_img[:, :, 2] = 255  # Red channel in BGR
    out.write(test_img)
    out.release()

    # BGR24
    cfg_bgr = CameraConfig(
        camera_id="cam_file_bgr",
        source_type=SourceType.FILE,
        width=width,
        height=height,
        fps=float(fps),
        file_path=video_path,
        pixel_format=PixelFormat.BGR24,
    )
    with FileCameraSource(cfg_bgr, loop=True) as src_bgr:
        f_bgr = src_bgr.capture_frame()
        assert f_bgr is not None
        assert f_bgr.metadata.pixel_format == PixelFormat.BGR24
        assert f_bgr.payload.shape == (height, width, 3)

    # GRAY8
    cfg_gray = CameraConfig(
        camera_id="cam_file_gray",
        source_type=SourceType.FILE,
        width=width,
        height=height,
        fps=float(fps),
        file_path=video_path,
        pixel_format=PixelFormat.GRAY8,
    )
    with FileCameraSource(cfg_gray, loop=True) as src_gray:
        f_gray = src_gray.capture_frame()
        assert f_gray is not None
        assert f_gray.metadata.pixel_format == PixelFormat.GRAY8
        assert f_gray.payload.shape == (height, width)


def test_manager_source_exception_recorded_in_metrics() -> None:
    """Verify exceptions during frame capture are recorded in metrics before propagating."""
    mgr = CameraManager()

    class FaultySource:
        camera_id = "faulty_cam"
        is_running = True

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def capture_frame(self) -> Frame | None:
            raise RuntimeError("Simulated optical sensor read hardware failure")

    mgr.register_source(FaultySource())  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="Simulated optical sensor read hardware failure"):
        mgr.ingest_next_frame("faulty_cam")

    snap = mgr.get_telemetry_snapshot("faulty_cam")
    assert snap["source_errors"] == 1
    assert snap["frames_produced"] == 0

    mgr.shutdown()
