# Agentic System Architecture (`.agents/`)

This directory contains the operational rules, quality specifications, and procedural workflows governing all AI coding agents operating within the **Autonomous Agentic AI Home Guard** repository.

---

## 1. File Structure & Ownership

```text
.agents/
├── README.md                  # This file: system explanation, discovery, and maintenance
├── rules/
│   ├── implementation.md      # Code quality, typing standards, and dependency rules
│   ├── verification.md        # Test suite, Ruff, Mypy, and evidence requirements
│   └── security.md            # Untrusted inputs, secret hygiene, and simulation safety
└── workflows/
    ├── implement.md           # 4-step workflow: Plan -> Implement -> Verify -> Report
    └── phase-gate.md          # Comprehensive audit, memory update, and handoff gate
```

### Document Authority Map

| Document | Authority / Scope | Loading Lifecycle |
| :--- | :--- | :--- |
| **`AGENTS.md` (root)** | Non-negotiable operational invariants (Git prohibition, `.venv`, phase boundaries) | **Always Active** (auto-injected by Antigravity) |
| **`AGENT_MEMORY.md` (root)** | Current active phase, verified implementation state, confirmed decisions | Checked at the start of every task |
| **`PROJECT_SPEC.md` (root)** | Master product specifications, architecture, and technology stack | Authoritative reference for domain features |
| **`.agents/rules/*.md`** | Detailed standards for code quality, verification, and security | **On-Demand** (loaded only when relevant) |
| **`.agents/workflows/*.md`** | Standardized operational procedures for implementation & phase gates | **On-Demand** (read when executing workflows) |

---

## 2. Antigravity Discovery & Loading Behavior

1. **Root Instructions (`AGENTS.md`)**:
   Antigravity automatically discovers and injects `AGENTS.md` from the repository root into the active conversation context as a permanent workspace rule (`<user_rules>`). This file is kept lean (~60–80 lines) to avoid context window overhead.
2. **Modular Rules (`.agents/rules/`)**:
   These files encapsulate in-depth domain standards. Agents load them selectively via read tools (`view_file`) when working on corresponding tasks (e.g. loading `security.md` when altering input schemas).
3. **Procedural Workflows (`.agents/workflows/`)**:
   Workflows provide explicit runbooks. In the Antigravity IDE and CLI, markdown files under `workflows/` serve as standardized operational runbooks referenced by `AGENTS.md`. Agents inspect them on-demand when planning changes or conducting phase gate audits.

---

## 3. Selective Context Retrieval Strategy

To maximize reasoning accuracy and token efficiency:
1. **Task Kickoff**: The agent relies on the already-loaded root `AGENTS.md` and reads `AGENT_MEMORY.md` to identify the active phase and permitted task.
2. **Targeted Loading**: Rather than reading all documentation files, the agent retrieves only the specific rule or workflow relevant to the current task:
   - For code refactoring or adding functions: load `rules/implementation.md`.
   - For writing tests or running quality gates: load `rules/verification.md`.
   - For input parsing, network payloads, or action dispatch: load `rules/security.md`.
   - For step-by-step feature implementation: follow `workflows/implement.md`.
   - For phase transition audits: follow `workflows/phase-gate.md`.
3. **Targeted Code Inspection**: Read only the specific target files and their direct callers/tests using slice notation or targeted tools. Avoid blanket workspace directory listings or dumping unrelated modules.

---

## 4. Maintenance Guidelines

- **No Duplication**: When editing standards, update only the authoritative file. Do not copy rules across multiple files.
- **Keep `AGENTS.md` Lean**: Only add rules to the root `AGENTS.md` if they must apply universally to every single agent interaction. Specialized instructions belong in `.agents/rules/`.
- **Preserve Links**: Ensure all cross-document links between `AGENTS.md`, `AGENT_MEMORY.md`, `PROJECT_SPEC.md`, and `.agents/` remain accurate relative markdown paths.
