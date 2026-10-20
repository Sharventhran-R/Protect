# Project Phase Gates & Acceptance Criteria

Every milestone in the **Autonomous Agentic AI Home Guard** development lifecycle is guarded by an explicit phase gate. 

> **MANDATORY POLICY**: No agent or developer may begin implementation on a subsequent phase until all acceptance criteria of the current phase are verified and the user has explicitly authorized the phase transition.

---

## Phase Overview Matrix

| Phase | Phase Name | Primary Objective | Gate Status |
| :---: | :--- | :--- | :---: |
| **0** | **Engineering Foundation & Agent Guardrails** | Minimal reproducible environment, strict guardrails, health baseline | **ACTIVE / READY FOR AUDIT** |
| **1** | **Synthetic Camera & Frame Ingestion Engine** | Video generation, synthetic feeds, frame buffering | *Locked (Awaiting Approval)* |
| **2** | **Object Detection & Multi-Object Tracking** | CPU YOLO inference, ByteTrack persistence, trajectory vectors | *Locked* |
| **3** | **Behavioral Classifier & Event Pipeline** | Spatial-temporal heuristics, security event schemas, async bus | *Locked* |
| **4** | **Agent Reasoning & Incident Synthesis** | LangGraph state loop, local Ollama LLM threat assessment | *Locked* |
| **5** | **Deterministic Policy Engine & Action Dispatch** | Deterministic safety gates, rate limiters, mocked actuators | *Locked* |
| **6** | **Operator Dashboard & Incident Playback** | React/Vite/Tailwind UI, real-time event stream, simulation replay | *Locked* |
| **7** | **System Hardening & Observability** | Metrics, telemetry, incident replay audit, end-to-end regression | *Locked* |

---

## Detailed Phase Gate Specifications

### Phase 0: Engineering Foundation & Agent Guardrails
- **Objective**: Establish a clean, reproducible, testable development environment and establish strict architectural and agentic-coding guardrails.
- **Scope**:
  - `pyproject.toml`, `.gitignore`, `.env.example`.
  - Mandatory instructions: `AGENTS.md`, `AGENT_MEMORY.md`.
  - Master specs: `PROJECT_SPEC.md`, `docs/`.
  - Minimal typed health status module: `src/home_guard/health.py`.
  - Unit tests: `tests/test_health.py`.
- **Exit Criteria**:
  - [x] Repository inspected; existing user work preserved.
  - [x] Package installs into `.venv` in editable mode without error.
  - [x] Pytest passes 100% on unit tests.
  - [x] Ruff check passes with 0 lint violations.
  - [x] Ruff format passes check mode with 0 formatting discrepancies.
  - [x] Mypy passes in strict mode with 0 type errors.
  - [x] Zero Git commands executed by agent.
  - [x] User explicitly reviews and authorizes Phase 1 kickoff.

---

### Phase 1: Synthetic Camera & Frame Ingestion Engine
- **Objective**: Provide a deterministic simulation feed that generates or reads recorded video streams without requiring real cameras.
- **Exit Criteria**:
  - Synthetic video generator produces test frames with simulated objects (cars, pedestrians, packages).
  - File-based video reader handles MP4/AVI files at target framerates.
  - Frame buffers drop zero frames under standard CPU load.
  - All Phase 0 quality checks (tests, ruff, mypy) remain 100% passing.
  - Phase 1 report presented and user approval granted.

---

### Phase 2: Object Detection & Multi-Object Tracking
- **Objective**: Ingest frames, detect security-relevant entities on CPU (people, vehicles, animals, packages), and track them across frames with persistent IDs.
- **Exit Criteria**:
  - CPU-optimized YOLO detector running at reasonable FPS.
  - ByteTrack assigns persistent track IDs across temporary occlusions.
  - Trajectory vectors and dwell times calculated and attached to tracks.
  - Comprehensive unit and integration tests passing.

---

### Phase 3: Behavioral Classifier & Event Pipeline
- **Objective**: Classify spatial-temporal behaviors (e.g. loitering, perimeter breach, package theft) and publish structured immutable events.
- **Exit Criteria**:
  - Rule-based and lightweight classifier detects loitering ($>N$ seconds in zone).
  - Pydantic models for all security event types.
  - Asynchronous event bus delivers events reliably to consumer queues.

---

### Phase 4: Agent Reasoning & Incident Synthesis
- **Objective**: Orchestrate high-level incident narratives using LangGraph and a local Ollama LLM (Qwen2.5 / Llama 3.2).
- **Exit Criteria**:
  - LangGraph state machine correlates events across time and cameras into Incidents.
  - Local LLM evaluates threat levels and generates structured Action Proposals.
  - Zero arbitrary code execution capabilities granted to LLM.

---

### Phase 5: Deterministic Policy Engine & Action Dispatch
- **Objective**: Enforce deterministic safety gates and simulate actuator responses (floodlights, sirens, alerts).
- **Exit Criteria**:
  - Deterministic policy validator independently verifies armed status, rate limits, and escalation steps.
  - Unauthorized actions rejected with auditable rejection codes.
  - Simulated actuators log state changes accurately.

---

### Phase 6: Operator Dashboard & Incident Playback
- **Objective**: Provide a modern browser dashboard for security operators to review active cameras, incidents, and threat assessments.
- **Exit Criteria**:
  - React/TypeScript/Vite dashboard connects via WebSocket/REST.
  - Video feed playback and bounding box overlay render smoothly.
  - Operator manual override and armed status toggling functional.

---

### Phase 7: System Hardening & Observability
- **Objective**: Complete end-to-end simulation testing, benchmark metrics, telemetry, and regression validation.
- **Exit Criteria**:
  - Full automated scenario test suite passes for known attack vectors and normal activity.
  - Metrics and telemetry exported cleanly.
  - Final production-readiness review signed off.
