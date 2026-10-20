# AGENT_MEMORY.md — Persistent Project Memory

## 1. Project Purpose & Current Status
- **Project**: Autonomous Agentic AI Home Guard (`Protect`)
- **Purpose**: A simulation-first, autonomous intelligent home security system operating without requiring physical smart-home hardware, physical cameras, or a dedicated GPU.
- **Current Status**: **Phase 0 (Engineering Foundation & Agent Guardrails)** completed and verified. Agentic configuration in `.agents/` established.

---

## 2. Confirmed Architectural Decisions
- **Simulation-First Invariant**: All video processing, camera feeds, device triggers, and emergency dispatches will execute against simulated mocks and synthetic/recorded inputs.
- **Strict Decoupling**: Separation of perception, object tracking, behavior classification, LangGraph agent workflows, deterministic policy verification, and simulated actuators.
- **Deterministic Policy Safety Net**: Probabilistic LLM decisions cannot execute actions directly; all proposed actions must pass an independent, deterministic policy validator.
- **No Speculative Dependencies**: Foundation uses pure Python standard library for core domain logic and health checks in Phase 0. Future frameworks (FastAPI, OpenCV, LangGraph, etc.) are introduced strictly in their designated phases.
- **Package Layout**: Standard `src/home_guard` layout using `pyproject.toml` (PEP 621 / PEP 517).
- **Agent System**: Lean root `AGENTS.md` with modular on-demand rules in `.agents/rules/` and operational runbooks in `.agents/workflows/`.

---

## 3. Active Phase Status & Acceptance Criteria
- **Phase 0 Status**: **COMPLETED & VERIFIED** (Committed in `620f9fd`)
- **Phase 1 Status**: **LOCKED / PENDING USER AUTHORIZATION**
- **Canonical Phase 0 Verified Criteria** (Synchronized with `docs/phase-gates.md`):
  1. Repository inspected, user work preserved.
  2. Guardrails (`AGENTS.md`) and persistent memory (`AGENT_MEMORY.md`) active.
  3. Clean `pyproject.toml` with pytest, Ruff, and Mypy configured.
  4. Virtual environment (`.venv`) established with verified dependency installation.
  5. Minimal testable health module (`src/home_guard/health.py`) implemented with strict typing.
  6. Unit tests (`tests/test_health.py`) pass 100%.
  7. Ruff linting and formatting checks pass with 0 errors.
  8. Mypy strict type checks pass with 0 errors.
  9. `.gitignore` and `.env.example` prevent secret leaks and repository pollution.
  10. No Git commands executed by agents.
  11. Verification commands documented for Windows PowerShell.

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
│       ├── __init__.py        # Package exports and version
│       └── health.py          # Foundational health & status module
└── tests/
    └── test_health.py         # Unit tests for health module
```

---

## 5. Environment & Verification Commands (PowerShell)
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install development dependencies
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

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
- **Host Python Version**: The host environment runs Python 3.14.6 (`pythoncore-3.14-64`). While the project target is `requires-python = '>=3.12'`, all Phase 0 tooling (pytest, ruff, mypy) has been verified compatible on Python 3.14.
- **Future Phase 1 Dependency Compatibility**: OpenCV, PyTorch, or YOLO packages in Phase 1+ must be checked for binary wheel availability on Python 3.14 on Windows when Phase 1 is authorized.

---

## 7. Next Authorized Task
- **Awaiting User Approval** before starting Phase 1 (Synthetic Camera & Frame Ingestion Engine).

---

## 8. Explicit Constraints & Prohibited Operations
- **PROHIBITED**: Running any Git command (`git add`, `git commit`, `git checkout`, etc.).
- **PROHIBITED**: Installing packages into the global Python environment.
- **PROHIBITED**: Hardcoding credentials or committing `.env`.
- **PROHIBITED**: Bypassing safety checks, relaxing types with `Any`, or disabling linters.
- **PROHIBITED**: Implementing features or creating directories belonging to Phase 1 or later.
