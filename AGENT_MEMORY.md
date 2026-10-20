# AGENT_MEMORY.md — Persistent Project Memory

## 1. Project Purpose & Current Status
- **Project**: Autonomous Agentic AI Home Guard (`Protect`)
- **Purpose**: A simulation-first, autonomous intelligent home security system operating without requiring physical smart-home hardware, physical cameras, or a dedicated GPU.
- **Current Status**: **Phase 1 (Synthetic Camera & Frame Ingestion Engine)** undergoing final robustness verification and review audit. Implementation and extended test suite in progress.

---

## 2. Confirmed Architectural Decisions
- **Simulation-First Invariant**: All video processing, camera feeds, device triggers, and emergency dispatches execute against simulated mocks and synthetic/recorded inputs.
- **Strict Decoupling**: Separation of perception, object tracking, behavior classification, LangGraph agent workflows, deterministic policy verification, and simulated actuators.
- **Deterministic Policy Safety Net**: Probabilistic LLM decisions cannot execute actions directly; all proposed actions must pass an independent, deterministic policy validator.
- **Camera Subsystem Architecture (Phase 1)**:
  - Bounded, thread-safe frame buffer (`FrameBuffer`) supporting `DROP_OLDEST` and `REJECT_NEWEST` overflow policies, with monotonic timed condition-wait pop logic.
  - Strongly-typed `CameraConfig`, `FrameMetadata`, and `Frame` models with strict dimensional and dtype validation.
  - Deterministic CPU-only `SyntheticCameraSource` generating reproducible frames with moving geometric entities and sequence patterns without wall-clock sleep dependencies.
  - Optional `FileCameraSource` decoding local MP4/AVI files via OpenCV with graceful decoder availability checking, empty/corrupt file rejection, and resource cleanup.
  - `CameraManager` providing centralized registry, lifecycle control, and downstream consumer API (`get_next_frame`) for Phase 2.
- **Package Layout**: Standard `src/home_guard` layout using `pyproject.toml` (PEP 621 / PEP 517).
- **Agent System**: Lean root `AGENTS.md` with modular on-demand rules in `.agents/rules/` and operational runbooks in `.agents/workflows/`.

---

## 3. Active Phase Status & Acceptance Criteria
- **Phase 0 Status**: **COMPLETED & VERIFIED** (Committed in `620f9fd`)
- **Phase 1 Status**: **UNDERGOING FINAL ROBUSTNESS VERIFICATION** (Targeted code review improvements & missing test coverage being verified; pending human approval)
- **Phase 2 Status**: **LOCKED / PENDING USER AUTHORIZATION**

### Phase 1 Criteria Verification Evidence Status
1. [x] Camera contracts and domain models (`CameraConfig`, `FrameMetadata`, `Frame`) implemented with strict validation.
2. [x] Deterministic synthetic camera source generates reproducible frames from identical seeds without GPU/camera hardware.
3. [x] Explicit timing behavior without wall-clock sleeps in synthetic frame generation.
4. [x] File-backed video source (`FileCameraSource`) implemented with OpenCV, non-looping EOF handling, empty/corrupt file rejection, and cleanup.
5. [x] Bounded frame buffer (`FrameBuffer`) enforces capacity and overflow policies (`DROP_OLDEST`, `REJECT_NEWEST`) with thread-safe monotonic timed waits.
6. [x] Dropped-frame and telemetry tracking (`CameraMetrics`) operational, recording source errors and invalid frames.
7. [x] Camera registry and lifecycle coordinator (`CameraManager`) prevents duplicate IDs, manages isolation, and provides idempotent repeated shutdown.
8. [x] Multi-camera isolation verified with independent sequence numbers and buffers.
9. [x] Downstream consumer interface (`get_next_frame`) provides clean frames for Phase 2.
10. [x] Zero Phase 2+ features (YOLO, ByteTrack, LangGraph, etc.) implemented.
11. [x] Full test suite execution with extended coverage (40 passed: 4 Phase 0 health + 36 Phase 1 camera).
12. [x] Ruff lint passes with 0 errors.
13. [x] Ruff format passes check with 0 discrepancies (25 files formatted).
14. [x] Mypy passes in strict mode with 0 type errors across 12 source files.
15. [x] Zero Git commands executed by agent.
16. [x] Phase 2 entry remains locked pending explicit user authorization.

---

## 4. Repository Structure & Key Entry Points
```text
Protect/
├── AGENTS.md                  # Mandatory agent instructions and boundaries
├── AGENT_MEMORY.md            # Persistent project state and verified decisions
├── PROJECT_SPEC.md            # Master architectural specification
├── README.md                  # User-facing onboarding and overview
├── pyproject.toml             # Build system, dependencies, and tool configs
├── .gitignore                 # Artifact, cache, and secret exclusions
├── .env.example               # Non-sensitive configuration template
├── .agents/                   # Agentic operational system
│   ├── README.md              # Agent architecture and retrieval guide
│   ├── rules/                 # Modular on-demand rules
│   │   ├── implementation.md  # Code standards, types, and dependencies
│   │   ├── verification.md    # Testing, linting, and evidence requirements
│   │   └── security.md        # Safety boundaries and secret hygiene
│   └── workflows/             # Procedural runbooks
│       ├── implement.md       # Standard 4-step implementation workflow
│       └── phase-gate.md      # Phase gate audit and handoff workflow
├── docs/
│   ├── architecture.md        # Subsystem boundaries and data flow
│   ├── development.md         # Windows PowerShell setup and test workflow
│   └── phase-gates.md         # Phase definitions, gates, and acceptance tests
├── src/
│   └── home_guard/
│       ├── __init__.py        # Package exports (health + camera entry points)
│       ├── health.py          # Foundational health & status module
│       └── camera/            # Phase 1: Camera ingestion & synthetic engine
│           ├── __init__.py    # Camera subsystem interface exports
│           ├── models.py      # CameraConfig, FrameMetadata, Frame, exceptions
│           ├── protocols.py   # CameraSource and FrameConsumer protocols
│           ├── synthetic.py   # Deterministic CPU-only synthetic generator
│           ├── file_source.py # Local video file decoding with OpenCV
│           ├── buffer.py      # Bounded frame buffer with overflow policies
│           ├── metrics.py     # Thread-safe telemetry counters
│           └── manager.py     # CameraManager registry and consumer interface
└── tests/
    ├── test_health.py         # Phase 0: Health module tests (4 passed)
    └── test_camera.py         # Phase 1: Camera subsystem test suite (27 passed)
```

---

## 5. Environment & Verification Commands (PowerShell)
```powershell
# Run tests
.\.venv\Scripts\pytest.exe -v

# Check code formatting
.\.venv\Scripts\ruff.exe format --check .

# Lint code
.\.venv\Scripts\ruff.exe check .

# Check types
.\.venv\Scripts\mypy.exe src tests
```

---

## 6. Known Issues & Unresolved Decisions
- **Host Python Environment**: Python 3.14.6 AMD64 on Windows.
- **Verified Phase 1 Dependencies**: `numpy==2.5.4` and `opencv-python==5.0.0.93` verified fully compatible and operational.
- **Phase 2 Compatibility Check**: When Phase 2 is authorized, binary wheel availability for YOLO/PyTorch/ByteTrack on Python 3.14 on Windows must be evaluated.

---

## 7. Next Authorized Task
- **Awaiting User Approval** before starting Phase 2 (Object Detection & Multi-Object Tracking).

---

## 8. Explicit Constraints & Prohibited Operations
- **PROHIBITED**: Running any Git command (`git add`, `git commit`, `git checkout`, etc.).
- **PROHIBITED**: Installing packages into the global Python environment.
- **PROHIBITED**: Hardcoding credentials or committing `.env`.
- **PROHIBITED**: Bypassing safety checks, relaxing types with `Any`, or disabling linters.
- **PROHIBITED**: Implementing features or creating directories belonging to Phase 2 or later.
