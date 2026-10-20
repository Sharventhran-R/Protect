# Workflow: Phase Gate Audit & Handoff

This procedure governs the verification and authorization handoff required to conclude an active phase before transitioning to the next phase.

---

## 1. Prerequisites
- All functional and architectural tasks assigned to the active phase must be implemented.
- No code, dependencies, or directory placeholders belonging to future phases may exist.
- Review the authoritative acceptance criteria in `docs/phase-gates.md` for the active phase.

---

## 2. Comprehensive Quality Audit (PowerShell)
Execute the complete quality test suite from the repository root:

```powershell
# 1. Full unit & integration test run
.\.venv\Scripts\pytest.exe -v

# 2. Complete Ruff format verification
.\.venv\Scripts\ruff.exe format --check .

# 3. Complete Ruff linting
.\.venv\Scripts\ruff.exe check .

# 4. Strict static type analysis across all packages and tests
.\.venv\Scripts\mypy.exe src tests

# 5. Core package import and health check
.\.venv\Scripts\python.exe -c "import home_guard; print(f'Ready: {home_guard.__version__}')"
```

All 5 commands must return exit code 0. Zero test failures, zero lint warnings, and zero type errors are tolerated.

---

## 3. Persistent Memory & Documentation Audit
1. **Update `AGENT_MEMORY.md`**:
   - Record completed milestones under "Current Status".
   - Document any new confirmed architectural decisions.
   - List verified packages and dependencies.
   - Set "Next Authorized Task" to denote awaiting user authorization for the next phase.
2. **Verify Cross-References**: Ensure all file paths referenced in documentation exist and are accurate.

---

## 4. Phase Gate Report & Handoff
Present a structured Phase Gate Report to the user containing:
1. **Phase Summary**: Deliverables produced during the phase.
2. **Criteria Checklist**: Each acceptance criterion from `docs/phase-gates.md` marked PASS with supporting evidence.
3. **Audit Log**: Verification commands and actual terminal outputs.
4. **Explicit Transition Halt**: State clearly that the phase gate is complete and that the subsequent phase is locked pending explicit user authorization.

> **CRITICAL GUARDRAIL**: Do NOT start the subsequent phase automatically. The agent must halt and wait for the user to approve the transition.
