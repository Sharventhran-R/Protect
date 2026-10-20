# Mandatory Agent Instructions & Operational Guardrails

All AI coding agents, autonomous subagents, and contributors operating within this repository MUST strictly follow the directives in this document. This file is automatically loaded into your context.

---

## 1. Absolute Invariants

- **PROHIBITED Git Operations**: Under NO circumstances run Git commands (`git add`, `git commit`, `git push`, `git checkout`, `git status`, etc.) or alter `.git` metadata. The human user exclusively owns all Git operations.
- **Mandatory Virtual Environment**: All Python execution, testing, and dependency tools MUST run using the local virtual environment at `.venv/` (PowerShell: `.\.venv\Scripts\<tool>.exe`). Never install dependencies globally.
- **Strict Phase Discipline**: Implement ONLY the explicitly authorized phase and task defined in [AGENT_MEMORY.md](AGENT_MEMORY.md). Never jump ahead, create future-phase modules, or install speculative infrastructure.
- **Safety by Construction**: Treat all inputs (video, sensor data, LLM outputs) as untrusted. LLMs must NEVER execute arbitrary shell commands or code. All actions must pass deterministic policy validation. Physical hardware and emergency services MUST remain mocked.

---

## 2. Progressive Context Retrieval Strategy

To maximize reasoning accuracy and token efficiency, do NOT load all project documents indiscriminately:

1. **Task Start**:
   - Inspect [AGENT_MEMORY.md](AGENT_MEMORY.md) to confirm the active phase and permitted task.
   - Retrieve ONLY the specific section of [PROJECT_SPEC.md](PROJECT_SPEC.md) or phase gate criteria in [docs/phase-gates.md](docs/phase-gates.md) relevant to the immediate task.
2. **On-Demand Rule Loading**:
   - Before implementing or refactoring code: load [.agents/rules/implementation.md](.agents/rules/implementation.md).
   - Before running tests or reporting verification: load [.agents/rules/verification.md](.agents/rules/verification.md).
   - Before handling external inputs, model outputs, or actions: load [.agents/rules/security.md](.agents/rules/security.md).
3. **Workflow Execution**:
   - For standard feature/bugfix changes, follow [.agents/workflows/implement.md](.agents/workflows/implement.md).
   - For phase transition audits and reviews, follow [.agents/workflows/phase-gate.md](.agents/workflows/phase-gate.md).
4. **Targeted Code Inspection**:
   - Inspect only files directly touched by the change and their immediate callers/tests.
   - Avoid blanket directory listings and entire-codebase dumps.

---

## 3. Mandatory Quality Standards

- **Strict Static Typing**: Comprehensive type hints on all public signatures. No unconstrained `Any` or broad type ignores without documented justification.
- **Automated Verification**: Before declaring any task complete, execute the quality suite via local `.venv`:
  - `pytest`: `.\.venv\Scripts\pytest.exe -v` (100% pass)
  - `ruff format`: `.\.venv\Scripts\ruff.exe format --check .` (0 errors)
  - `ruff lint`: `.\.venv\Scripts\ruff.exe check .` (0 errors)
  - `mypy`: `.\.venv\Scripts\mypy.exe src tests` (0 errors)
- **Factual Integrity**: Never report a check passed unless it was executed and returned exit code 0.
