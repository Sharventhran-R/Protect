# Workflow: Feature & Bugfix Implementation

A concise, reusable 4-step procedure for implementing any code change or feature within the authorized phase.

---

## Step 1: Plan & Selective Context Retrieval
1. **Check Authorization**: Inspect `AGENT_MEMORY.md` to confirm the active phase and currently permitted task. Do not implement out-of-phase work.
2. **Selective Rule Retrieval**:
   - For code structure/typing: review [.agents/rules/implementation.md](../rules/implementation.md).
   - For security/input validation: review [.agents/rules/security.md](../rules/security.md).
   - For test expectations: review [.agents/rules/verification.md](../rules/verification.md).
3. **Inspect Target Files**: Read only the files, callers, and tests directly affected by the change. Avoid dumping entire directory trees.
4. **Formulate Plan**: Identify proposed edits, potential regressions, and verification commands.

---

## Step 2: Implement Within Guardrails
1. **Targeted Edits**: Apply precise code modifications. Keep functions cohesive and maintain strict static type annotations.
2. **Environment Invariant**: Execute tooling strictly within `.venv/`. Never run global Python or pip commands.
3. **Safety Invariant**: Maintain deterministic policy boundaries and mocked hardware interfaces.
4. **Git Prohibition**: Do not execute any Git commands (`git add`, `git commit`, `git checkout`, etc.). All Git operations are reserved for the user.

---

## Step 3: Verify with Local Tooling (PowerShell)
Execute and verify exit code 0 for all applicable checks:

```powershell
# 1. Run unit tests
.\.venv\Scripts\pytest.exe -v

# 2. Check formatting
.\.venv\Scripts\ruff.exe format --check .

# 3. Static linting
.\.venv\Scripts\ruff.exe check .

# 4. Strict static type analysis
.\.venv\Scripts\mypy.exe src tests
```

If any check fails, inspect the error output, apply targeted corrections, and re-run until all checks pass.

---

## Step 4: Report Results
Provide a clear, factual report covering:
1. **Summary**: What was changed and why.
2. **Files Changed**: Exact paths and descriptions of modified/created files.
3. **Verification Evidence**: Commands executed, exit codes, and output summaries.
4. **Limitations & Next Steps**: Disclose any skipped items or remaining tasks within the phase.
