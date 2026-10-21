"""Deterministic unit tests for perception domain models, bounding box math, and protocols."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from home_guard.camera.models import Frame, FrameMetadata, PixelFormat
from home_guard.perception import (
    BoundingBox,
    Detection,
    DetectionErrorCode,
    DetectionErrorDetail,
    DetectionResult,
    InvalidBoundingBoxError,
    InvalidDetectionError,
    InvalidDetectionResultError,
    MultiObjectTracker,
    ObjectDetector,
    TrackingResultProtocol,
)


@pytest.fixture
def sample_metadata() -> FrameMetadata:
    """Fixture providing valid FrameMetadata for testing."""
    return FrameMetadata(
        camera_id="cam_porch_01",
        sequence_number=42,
        timestamp_ns=1_767_268_800_000_000_000,
        timestamp_utc="2026-01-01T12:00:00+00:00",
        width=640,
        height=480,
        pixel_format=PixelFormat.RGB24,
        scene_label="porch",
    )


@pytest.fixture
def sample_frame(sample_metadata: FrameMetadata) -> Frame:
    """Fixture providing valid Frame for testing."""
    payload = np.zeros((480, 640, 3), dtype=np.uint8)
    return Frame(metadata=sample_metadata, payload=payload)


# ============================================================================
# 1. BoundingBox Tests
# ============================================================================


def test_bounding_box_valid_geometry_and_properties() -> None:
    """Verify BoundingBox properties and float coordinate conversion."""
    box = BoundingBox(x1=10, y1=20, x2=50, y2=80)

    assert box.x1 == 10.0
    assert box.y1 == 20.0
    assert box.x2 == 50.0
    assert box.y2 == 80.0
    assert isinstance(box.x1, float)
    assert isinstance(box.y1, float)
    assert isinstance(box.x2, float)
    assert isinstance(box.y2, float)

    # Derived geometric properties
    assert box.width == 40.0
    assert box.height == 60.0
    assert box.area == 2400.0
    assert box.center == (30.0, 50.0)
    assert box.aspect_ratio == pytest.approx(40.0 / 60.0)


@pytest.mark.parametrize(
    ("x1", "y1", "x2", "y2"),
    [
        (float("nan"), 0.0, 10.0, 10.0),
        (0.0, float("nan"), 10.0, 10.0),
        (0.0, 0.0, float("nan"), 10.0),
        (0.0, 0.0, 10.0, float("nan")),
        (float("inf"), 0.0, 10.0, 10.0),
        (0.0, float("inf"), 10.0, 10.0),
        (0.0, 0.0, float("inf"), 10.0),
        (0.0, 0.0, 10.0, float("inf")),
        (float("-inf"), 0.0, 10.0, 10.0),
        (True, 0.0, 10.0, 10.0),
        (0.0, False, 10.0, 10.0),
        (0.0, 0.0, True, 10.0),
        (0.0, 0.0, 10.0, False),
        (-1.0, 0.0, 10.0, 10.0),
        (0.0, -0.5, 10.0, 10.0),
        (10.0, 0.0, 10.0, 10.0),  # zero width
        (15.0, 0.0, 10.0, 10.0),  # inverted width
        (0.0, 20.0, 10.0, 20.0),  # zero height
        (0.0, 25.0, 10.0, 20.0),  # inverted height
    ],
)
def test_bounding_box_invalid_coordinates_raise(x1: float, y1: float, x2: float, y2: float) -> None:
    """Verify BoundingBox rejects non-finite, boolean, negative, and inverted coordinates."""
    with pytest.raises(InvalidBoundingBoxError):
        BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)


def test_bounding_box_non_numeric_types_raise() -> None:
    """Verify BoundingBox rejects non-numeric types."""
    with pytest.raises(InvalidBoundingBoxError):
        BoundingBox(x1="10", y1=20, x2=50, y2=80)  # type: ignore[arg-type]


def test_bounding_box_immutability() -> None:
    """Verify BoundingBox is frozen and immutable."""
    box = BoundingBox(x1=10, y1=20, x2=50, y2=80)
    with pytest.raises(FrozenInstanceError):
        box.x1 = 15.0  # type: ignore[misc]


def test_bounding_box_iou_calculations() -> None:
    """Verify mathematically correct IoU calculations across geometric configurations."""
    box_a = BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)

    # 1. Identical boxes
    assert box_a.iou(box_a) == 1.0
    box_a_clone = BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
    assert box_a.iou(box_a_clone) == 1.0

    # 2. Completely disjoint boxes (horizontal separation)
    box_disjoint_x = BoundingBox(x1=20.0, y1=0.0, x2=30.0, y2=10.0)
    assert box_a.iou(box_disjoint_x) == 0.0

    # 3. Completely disjoint boxes (vertical separation)
    box_disjoint_y = BoundingBox(x1=0.0, y1=20.0, x2=10.0, y2=30.0)
    assert box_a.iou(box_disjoint_y) == 0.0

    # 4. Touching edges (half-open intersection has zero area)
    box_touching_right = BoundingBox(x1=10.0, y1=0.0, x2=20.0, y2=10.0)
    assert box_a.iou(box_touching_right) == 0.0
    box_touching_bottom = BoundingBox(x1=0.0, y1=10.0, x2=10.0, y2=20.0)
    assert box_a.iou(box_touching_bottom) == 0.0

    # 5. Partially overlapping boxes
    # box_a: [0, 0, 10, 10], area = 100
    # box_b: [5, 5, 15, 15], area = 100
    # intersection: [5, 5, 10, 10], area = 25
    # union: 100 + 100 - 25 = 175
    # iou: 25 / 175 = 1 / 7
    box_b = BoundingBox(x1=5.0, y1=5.0, x2=15.0, y2=15.0)
    assert box_a.iou(box_b) == pytest.approx(25.0 / 175.0)
    assert box_b.iou(box_a) == pytest.approx(25.0 / 175.0)

    # 6. Nested boxes (inner completely inside outer)
    # outer: [0, 0, 10, 10], area = 100
    # inner: [2, 2, 6, 6], area = 16
    # intersection: 16
    # union: 100 + 16 - 16 = 100
    # iou: 16 / 100 = 0.16
    box_inner = BoundingBox(x1=2.0, y1=2.0, x2=6.0, y2=6.0)
    assert box_a.iou(box_inner) == pytest.approx(0.16)

    # 7. Type check
    with pytest.raises(TypeError):
        box_a.iou("not_a_box")  # type: ignore[arg-type]


def test_bounding_box_clip_to_image_success() -> None:
    """Verify clip_to_image clips boxes intersecting image boundaries."""
    # Fully inside
    box_inside = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    clipped = box_inside.clip_to_image(width=100, height=100)
    assert clipped == box_inside

    # Overhanging right edge
    box_right = BoundingBox(x1=80.0, y1=20.0, x2=140.0, y2=80.0)
    clipped_right = box_right.clip_to_image(width=100, height=100)
    assert clipped_right == BoundingBox(x1=80.0, y1=20.0, x2=100.0, y2=80.0)

    # Overhanging bottom edge
    box_bottom = BoundingBox(x1=10.0, y1=70.0, x2=50.0, y2=130.0)
    clipped_bottom = box_bottom.clip_to_image(width=100, height=100)
    assert clipped_bottom == BoundingBox(x1=10.0, y1=70.0, x2=50.0, y2=100.0)

    # Overhanging both right and bottom edges
    box_both = BoundingBox(x1=60.0, y1=60.0, x2=150.0, y2=150.0)
    clipped_both = box_both.clip_to_image(width=100, height=100)
    assert clipped_both == BoundingBox(x1=60.0, y1=60.0, x2=100.0, y2=100.0)


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (0, 100),
        (100, 0),
        (-10, 100),
        (100, -10),
        (True, 100),
        (100, False),
        (float("nan"), 100),
        (100, float("inf")),
    ],
)
def test_bounding_box_clip_invalid_image_dimensions_raise(width: int, height: int) -> None:
    """Verify clip_to_image rejects non-positive or non-finite image dimensions."""
    box = BoundingBox(x1=10.0, y1=10.0, x2=50.0, y2=50.0)
    with pytest.raises(ValueError):
        box.clip_to_image(width=width, height=height)


@pytest.mark.parametrize(
    ("x1", "y1", "x2", "y2"),
    [
        (110.0, 10.0, 150.0, 50.0),  # Completely to the right of width=100
        (10.0, 110.0, 50.0, 150.0),  # Completely below height=100
        (100.0, 10.0, 150.0, 50.0),  # Touching right edge (x1 == width)
        (10.0, 100.0, 50.0, 150.0),  # Touching bottom edge (y1 == height)
    ],
)
def test_bounding_box_clip_no_intersection_raises(
    x1: float, y1: float, x2: float, y2: float
) -> None:
    """Verify clip_to_image clearly rejects boxes with no positive-area intersection."""
    box = BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
    with pytest.raises(InvalidBoundingBoxError, match="no positive-area intersection"):
        box.clip_to_image(width=100, height=100)


# ============================================================================
# 2. Detection Tests
# ============================================================================


def test_detection_valid_creation() -> None:
    """Verify creation of a valid Detection contract."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det = Detection(class_id=0, label="person", confidence=0.95, box=box)

    assert det.class_id == 0
    assert det.label == "person"
    assert det.confidence == 0.95
    assert det.box == box


def test_detection_label_whitespace_trimming() -> None:
    """Verify Detection trims surrounding whitespace on labels."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det = Detection(class_id=1, label="  vehicle_car   ", confidence=0.88, box=box)
    assert det.label == "vehicle_car"


def test_detection_confidence_boundaries() -> None:
    """Verify confidence allows exact boundaries 0.0 and 1.0, including int 0 and 1."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)

    det_min = Detection(class_id=0, label="person", confidence=0.0, box=box)
    assert det_min.confidence == 0.0

    det_max = Detection(class_id=0, label="person", confidence=1.0, box=box)
    assert det_max.confidence == 1.0

    det_int = Detection(class_id=0, label="person", confidence=1, box=box)
    assert det_int.confidence == 1.0
    assert isinstance(det_int.confidence, float)


@pytest.mark.parametrize(
    "conf",
    [
        -0.01,
        1.01,
        -10.0,
        100.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        False,
        "0.5",
    ],
)
def test_detection_invalid_confidence_raises(conf: float) -> None:
    """Verify Detection rejects invalid confidence values."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    with pytest.raises(InvalidDetectionError):
        Detection(class_id=0, label="person", confidence=conf, box=box)


@pytest.mark.parametrize("class_id", [-1, -99, True, False, 1.5, "0", None])
def test_detection_invalid_class_id_raises(class_id: int) -> None:
    """Verify Detection rejects negative, boolean, and non-integer class IDs."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    with pytest.raises(InvalidDetectionError):
        Detection(class_id=class_id, label="person", confidence=0.8, box=box)


@pytest.mark.parametrize("label", ["", "   ", "\t\n", None, 123])
def test_detection_blank_label_raises(label: str) -> None:
    """Verify Detection rejects empty or whitespace-only labels."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    with pytest.raises(InvalidDetectionError):
        Detection(class_id=0, label=label, confidence=0.8, box=box)


def test_detection_invalid_box_raises() -> None:
    """Verify Detection rejects non-BoundingBox objects."""
    with pytest.raises(InvalidDetectionError):
        Detection(class_id=0, label="person", confidence=0.8, box="not_a_box")  # type: ignore[arg-type]


def test_detection_immutability() -> None:
    """Verify Detection contract enforces immutability."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det = Detection(class_id=0, label="person", confidence=0.8, box=box)
    with pytest.raises(FrozenInstanceError):
        det.confidence = 0.99  # type: ignore[misc]


# ============================================================================
# 3. DetectionResult Tests
# ============================================================================


def test_detection_result_success_with_detections(sample_metadata: FrameMetadata) -> None:
    """Verify successful DetectionResult with non-empty detections."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det = Detection(class_id=0, label="person", confidence=0.92, box=box)

    res = DetectionResult(
        frame_metadata=sample_metadata,
        detections=(det,),
        latency_ms=12.5,
    )

    assert res.is_success is True
    assert res.is_failure is False
    assert res.error is None
    assert len(res.detections) == 1
    assert res.detections[0] == det
    assert res.latency_ms == 12.5

    # Verify frame identity forwarding
    assert res.camera_id == sample_metadata.camera_id
    assert res.sequence_number == sample_metadata.sequence_number
    assert res.timestamp_ns == sample_metadata.timestamp_ns
    assert res.timestamp_utc == sample_metadata.timestamp_utc


def test_detection_result_success_empty_detections(sample_metadata: FrameMetadata) -> None:
    """Verify successful DetectionResult with zero detections is valid and distinct."""
    res = DetectionResult.success(
        frame_metadata=sample_metadata,
        detections=(),
        latency_ms=8.0,
    )

    assert res.is_success is True
    assert res.is_failure is False
    assert res.error is None
    assert len(res.detections) == 0


def test_detection_result_explicit_failure_representation(sample_metadata: FrameMetadata) -> None:
    """Verify failed DetectionResult carries typed error details and is distinguishable."""
    res = DetectionResult.failure(
        frame_metadata=sample_metadata,
        error="Inference execution timed out",
        latency_ms=50.0,
    )

    assert res.is_success is False
    assert res.is_failure is True
    assert res.error is not None
    assert isinstance(res.error, DetectionErrorDetail)
    assert res.error.code == DetectionErrorCode.INFERENCE_FAILED
    assert res.error.message == "Inference execution timed out"
    assert len(res.detections) == 0


def test_detection_result_structured_error_detail(sample_metadata: FrameMetadata) -> None:
    """Verify DetectionResult accepts pre-formed DetectionErrorDetail."""
    err = DetectionErrorDetail(
        code=DetectionErrorCode.MODEL_NOT_INITIALIZED,
        message="Model weights not loaded into memory",
        exception_type="RuntimeError",
    )
    res = DetectionResult(
        frame_metadata=sample_metadata,
        detections=(),
        error=err,
    )

    assert res.is_failure is True
    assert res.error == err
    assert res.error.code == DetectionErrorCode.MODEL_NOT_INITIALIZED
    assert res.error.exception_type == "RuntimeError"


def test_detection_result_failed_cannot_contain_detections(
    sample_metadata: FrameMetadata,
) -> None:
    """Verify that a failed DetectionResult cannot contain detections."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det = Detection(class_id=0, label="person", confidence=0.9, box=box)

    with pytest.raises(InvalidDetectionResultError, match="cannot contain detections"):
        DetectionResult(
            frame_metadata=sample_metadata,
            detections=(det,),
            error="Model failed halfway",
        )


@pytest.mark.parametrize(
    "latency",
    [-1.0, -0.001, float("nan"), float("inf"), float("-inf"), True, False, "12.5"],
)
def test_detection_result_invalid_latency_raises(
    sample_metadata: FrameMetadata, latency: float
) -> None:
    """Verify DetectionResult rejects negative, non-finite, or boolean latencies."""
    with pytest.raises(InvalidDetectionResultError):
        DetectionResult(
            frame_metadata=sample_metadata,
            latency_ms=latency,
        )


def test_detection_result_frame_identity_mismatch_rejection(
    sample_metadata: FrameMetadata,
) -> None:
    """Verify DetectionResult rejects explicit field mismatches with frame_metadata."""
    # camera_id mismatch
    with pytest.raises(InvalidDetectionResultError, match="camera_id"):
        DetectionResult(
            frame_metadata=sample_metadata,
            camera_id="wrong_camera_id",
        )

    # sequence_number mismatch
    with pytest.raises(InvalidDetectionResultError, match="sequence_number"):
        DetectionResult(
            frame_metadata=sample_metadata,
            sequence_number=999,
        )

    # timestamp_ns mismatch
    with pytest.raises(InvalidDetectionResultError, match="timestamp_ns"):
        DetectionResult(
            frame_metadata=sample_metadata,
            timestamp_ns=12345,
        )

    # timestamp_utc mismatch
    with pytest.raises(InvalidDetectionResultError, match="timestamp_utc"):
        DetectionResult(
            frame_metadata=sample_metadata,
            timestamp_utc="2099-01-01T00:00:00+00:00",
        )


def test_detection_result_constructed_from_individual_fields() -> None:
    """Verify DetectionResult can be constructed from individual identity fields."""
    res = DetectionResult(
        camera_id="cam_backyard",
        sequence_number=10,
        timestamp_ns=100_000_000,
        timestamp_utc="2026-01-01T12:00:00+00:00",
        latency_ms=5.2,
    )

    assert res.camera_id == "cam_backyard"
    assert res.sequence_number == 10
    assert res.timestamp_ns == 100_000_000
    assert res.timestamp_utc == "2026-01-01T12:00:00+00:00"
    assert res.frame_metadata is not None
    assert res.frame_metadata.width == 640


def test_detection_result_missing_identity_raises() -> None:
    """Verify error if neither metadata nor complete identity fields given."""
    with pytest.raises(InvalidDetectionResultError, match="Either frame_metadata or complete"):
        DetectionResult(camera_id="cam_only")


def test_detection_result_immutable_detections_collection(sample_metadata: FrameMetadata) -> None:
    """Verify mutable list of detections is converted to an immutable tuple."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det1 = Detection(class_id=0, label="person", confidence=0.9, box=box)
    det2 = Detection(class_id=1, label="cat", confidence=0.8, box=box)

    mutable_list = [det1, det2]
    res = DetectionResult(frame_metadata=sample_metadata, detections=mutable_list)

    assert isinstance(res.detections, tuple)

    # Mutating original list does not affect result
    mutable_list.clear()
    assert len(res.detections) == 2

    # Mutating result raises FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        res.detections = ()  # type: ignore[misc]


def test_detection_result_invalid_detection_element_raises(sample_metadata: FrameMetadata) -> None:
    """Verify DetectionResult rejects non-Detection elements."""
    with pytest.raises(InvalidDetectionResultError):
        DetectionResult(
            frame_metadata=sample_metadata,
            detections=("not_a_detection",),  # type: ignore[arg-type]
        )


def test_detection_result_from_frame(sample_frame: Frame) -> None:
    """Verify DetectionResult can be created from a Phase 1 Frame object."""
    box = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    det = Detection(class_id=0, label="person", confidence=0.9, box=box)

    res = DetectionResult.success(
        frame_metadata=sample_frame.metadata,
        detections=[det],
        latency_ms=10.0,
    )

    assert res.camera_id == sample_frame.metadata.camera_id
    assert res.sequence_number == sample_frame.metadata.sequence_number
    assert res.timestamp_ns == sample_frame.metadata.timestamp_ns
    assert res.timestamp_utc == sample_frame.metadata.timestamp_utc


# ============================================================================
# 4. Protocol Structural Typing Tests
# ============================================================================


def test_object_detector_protocol_structural_typing(sample_frame: Frame) -> None:
    """Verify structural compliance with ObjectDetector protocol."""

    class ConformingDetector:
        def detect(self, frame: Frame) -> DetectionResult:
            return DetectionResult.success(frame_metadata=frame.metadata, detections=())

    class NonConformingDetector:
        def inference(self, frame: Frame) -> None:
            pass

    assert isinstance(ConformingDetector(), ObjectDetector)
    assert not isinstance(NonConformingDetector(), ObjectDetector)


def test_tracker_protocols_structural_typing(sample_metadata: FrameMetadata) -> None:
    """Verify structural compliance with MultiObjectTracker and TrackingResultProtocol."""

    class ConformingTrackingResult:
        @property
        def camera_id(self) -> str:
            return "cam1"

        @property
        def sequence_number(self) -> int:
            return 1

        @property
        def timestamp_ns(self) -> int:
            return 1_000_000

    class ConformingTracker:
        def update(self, detection_result: DetectionResult) -> TrackingResultProtocol:
            return ConformingTrackingResult()

        def reset(self) -> None:
            pass

    class IncompleteTracker:
        def update(self, detection_result: DetectionResult) -> None:
            pass

        # Missing reset()

    tracking_res = ConformingTrackingResult()
    assert isinstance(tracking_res, TrackingResultProtocol)

    tracker = ConformingTracker()
    assert isinstance(tracker, MultiObjectTracker)

    incomplete: object = IncompleteTracker()
    assert not isinstance(incomplete, MultiObjectTracker)
