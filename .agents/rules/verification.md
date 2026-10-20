# Verification & Quality Assurance Rules

These rules govern automated testing, static analysis, and verification reporting across all development tasks.

---

## 1. Test Strategy & Integrity
- **Genuine Unit & Integration Tests**: Write test cases covering normal execution, edge cases, error conditions, and data validation for all new modules.
- **Zero Tolerance for Broken Tests**: All existing and new tests must pass before completing any task.
- **Never Weaken Tests**: Never delete assertions, loosen validation thresholds, or skip tests merely to manufacture a green test run.
- **Fast & Isolated**: Tests must not rely on external networks, unmocked physical hardware, or live GPUs.

---

## 2. Tooling & Quality Gates (PowerShell)

All quality checks must be executed using the local `.venv` binaries on Windows:

| Check | PowerShell Command | Pass Criteria |
| :--- | :--- | :--- |
| **Unit Tests** | `.\.venv\Scripts\pytest.exe -v` | Exit code 0, 100% tests pass |
| **Code Formatting** | `.\.venv\Scripts\ruff.exe format --check .` | Exit code 0, 0 formatting discrepancies |
| **Static Linting** | `.\.venv\Scripts\ruff.exe check .` | Exit code 0, 0 lint errors |
| **Strict Typing** | `.\.venv\Scripts\mypy.exe src tests` | Exit code 0, 0 type errors |
| **Package Import** | `.\.venv\Scripts\python.exe -c "import home_guard; ..."` | Exit code 0, clean export validation |

---

## 3. Evidence & Reporting Standards
- **Factual Integrity Mandate**: Never report that a check, test, or linter passed unless it was explicitly executed and returned exit code 0.
- **Exact Command & Output**: Every verification report must quote the exact command executed, exit code, and stdout/stderr summary.
- **Full Transparency**: Disclose any skipped checks, environment limitations, or unresolved edge cases explicitly.
