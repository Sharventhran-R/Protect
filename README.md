# Protect — Autonomous Agentic AI Home Guard

An intelligent, simulation-first autonomous home security system powered by edge perception, behavioral analytics, and local agentic reasoning.

---

## 1. Project Purpose

The **Autonomous Agentic AI Home Guard** is designed to provide end-to-end intelligent physical security monitoring without relying on external cloud providers, real physical cameras, smart-home hardware, or a dedicated GPU. 

The architecture simulates visual feeds, performs frame-level perception and multi-object tracking, classifies behavioral anomalies, coordinates contextual reasoning using a local LLM, and enforces strict deterministic safety policies before dispatching simulated protective actions.

---

## 2. Current Status: Phase 0 Completed

This repository has completed **Phase 0 (Engineering Foundation & Agent Guardrails)**:
- Core developer tooling and virtual environment configured.
- Strict static typing, linting, and automated test runners enabled.
- Architectural boundaries and phase progression gates defined.
- Persistent project memory (`AGENT_MEMORY.md`) and mandatory agent instructions (`AGENTS.md`) enforced.
- Foundational health status module and unit tests implemented.

---

## 3. Prerequisites

- **OS**: Windows 10/11 (x64)
- **Shell**: PowerShell
- **Python**: Python 3.12+ (Host environment verified on Python 3.14.6)
- **Hardware**: Standard multi-core CPU (No GPU required)

---

## 4. Quickstart Setup (PowerShell)

### Clone & Navigate
```powershell
# Open PowerShell in the project directory
cd d:\PROJECTS\Protect
```

### Initialize Virtual Environment & Install Dependencies
```powershell
# 1. Create local virtual environment
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install package in editable mode with development tools
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

---

## 5. Verification Commands

Run the full verification suite directly:

```powershell
# Run unit tests
.\.venv\Scripts\pytest.exe

# Check code formatting
.\.venv\Scripts\ruff.exe format --check .

# Run static linter
.\.venv\Scripts\ruff.exe check .

# Run strict static type checking
.\.venv\Scripts\mypy.exe src tests

# Verify package import and health check
.\.venv\Scripts\python.exe -c "import home_guard; print(home_guard.get_health_status())"
```

---

## 6. Phase 0 Scope & Current Limitations

- **No Vision Models Yet**: YOLO object detectors, ByteTrack trackers, and OpenCV frame processors are planned for subsequent phases and are intentionally not installed in Phase 0.
- **No External Services**: Redis, Kafka, PostgreSQL, and Ollama are intentionally not required or installed during this foundation phase.
- **Pure Software Foundation**: All logic is currently pure Python standard library code designed to establish a rock-solid, reproducible baseline.

---

## 7. Next Authorized Phase

- **Phase 1: Synthetic Camera & Frame Ingestion Engine**
  - Synthesize virtual camera feeds (pedestrians, vehicles, delivery boxes).
  - File-based frame ingestion and FPS synchronization buffer.
  - *Status: Awaiting user authorization before kickoff.*

---

## 8. Documentation Index

- [AGENTS.md](AGENTS.md) — Mandatory agent coding guardrails and rules
- [AGENT_MEMORY.md](AGENT_MEMORY.md) — Persistent project decisions and state
- [PROJECT_SPEC.md](PROJECT_SPEC.md) — Master architectural specification
- [docs/architecture.md](docs/architecture.md) — Subsystem boundaries and safety gates
- [docs/development.md](docs/development.md) — Windows / PowerShell development workflow
- [docs/phase-gates.md](docs/phase-gates.md) — Phase definitions and acceptance criteria