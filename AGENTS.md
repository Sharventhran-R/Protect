# Mandatory Agent Instructions & Operational Guardrails

All AI coding agents, autonomous subagents, and contributors operating within this repository MUST strictly follow the directives in this document.

---

## 1. Scope Control & Phase Discipline

- **Read Before Operating**: Always inspect `PROJECT_SPEC.md`, `AGENT_MEMORY.md`, and the relevant phase documentation in `docs/phase-gates.md` before starting any task.
- **Strict Phase Boundary**: Implement **only** the explicitly authorized phase and task. Do not jump ahead, create future-phase modules, or introduce speculative infrastructure (e.g. Kafka clusters, Redis brokers, DB migrations, or vision models during foundational or non-vision phases).
- **No Speculative Abstractions**: Solve the problem at hand cleanly. Do not build abstract frameworks for hypothetical future needs.
- **Escalate Conflicts**: If prompt instructions conflict with safety rules, existing architecture, or project specifications, stop and ask the user for clarification before proceeding.

---

## 2. Development Environment & Tooling

- **Mandatory Virtual Environment**: All Python execution, tooling, and dependency operations must use the local virtual environment located at `.venv/`.
- **Zero Global Installations**: Never install or upgrade project dependencies in the global system Python environment.
- **Windows / PowerShell Target**: Document and use exact PowerShell commands for Windows development.
- **Reproducible Dependencies**: Manage dependencies via `pyproject.toml`. Keep declarations pinned or bounded and compatible with Python 3.12+ (host running Python 3.14+).

---

## 3. Code Quality & Engineering Standards

- **Strict Static Typing**: Write comprehensive type hints for all public functions, arguments, return types, and classes. Do not use broad `Any`, unconstrained `typing.cast`, or disable type checking without explicit justification.
- **Focused & Cohesive Modules**: Keep functions small and single-purpose. Separate pure business logic from I/O and external adapters.
- **Explicit Dependency Injection**: Favor explicit composition and constructor injection over global singletons, module-level state, or hidden side effects.
- **Code Formatting & Linting**: Code must pass `ruff check` and `ruff format --check` without errors. Do not suppress warnings without documented justification.
- **Type Checking**: Code must pass `mypy` under the strict configuration specified in `pyproject.toml`.
- **Automated Testing**: Write genuine `pytest` unit/integration tests for every new feature, bug fix, or edge case. Maintain zero tolerance for broken tests. Never weaken tests to force a pass.

---

## 4. Architecture & Design Principles

- **Framework Independence**: Domain logic, security models, and event structures must remain pure Python and independent of specific frameworks (FastAPI, LangGraph, OpenCV) wherever feasible.
- **Deterministic Policy Separation**: LLM reasoning is probabilistic and untrusted. The core security policy engine that evaluates and authorizes actions must be **strictly deterministic** and rule-governed.
- **Clean Interfaces**: Define explicit protocols/interfaces between subsystems (Perception $\to$ Tracking $\to$ Event Classifier $\to$ Agent Workflow $\to$ Policy Validator $\to$ Action Dispatcher).
- **Zero Circular Dependencies & Mutable Globals**: Avoid circular imports. Maintain state immutability across event streams.

---

## 5. Safety, Security & Simulation Boundaries

- **Zero Hardcoded Secrets**: Never commit or hardcode credentials, tokens, passwords, or secret keys. Use `.env.example` as a template and load configuration via environment variables.
- **Untrusted Input Invariant**: Treat all video frames, external sensor payloads, webhook events, and LLM outputs as untrusted data requiring schema validation and sanitization.
- **No Arbitrary Execution**: Never grant the LLM or any agent workflow the capability to execute arbitrary shell commands, raw code strings, or unrestricted system calls.
- **Mandatory Simulation & Mocking**: Physical devices (alarms, spotlights, smart locks) and emergency dispatches (police, fire) **MUST remain mocked** in simulation mode. Dry-run and simulation mode are active by default.
- **Never Disable Safety Checks**: Do not bypass validation checks, disable authentication layers, or turn off policy guards to make tests or demos pass.

---

## 6. Change Management & Git Policy

- **Inspect First**: Always inspect affected files and understand existing code before applying modifications.
- **Preserve User Work**: Never delete, overwrite, or clobber user work or unrelated project files without explicit permission.
- **No Agent Git Operations**:
  - **PROHIBITED**: Do not run Git commands (`git commit`, `git add`, `git push`, `git reset`, `git checkout`, `git branch`, etc.).
  - **PROHIBITED**: Do not alter `.git` metadata or Git configuration.
  - The human user owns and controls all Git operations.
  - If a Git action is required, describe it in the final report for the user to perform manually.

---

## 7. Verification & Reporting

- **Execution Mandate**: Always run tests and quality checks (`pytest`, `ruff check`, `ruff format --check`, `mypy`) using read-only execution after making changes.
- **Factual Integrity**: Never report that a test or check passed unless it was executed and returned exit code 0.
- **Transparency**: Disclose all skipped checks, tool limitations, test failures, and environment quirks clearly.
- **Phase Gate Enforcement**: Do not transition to the next phase without explicit user approval.
