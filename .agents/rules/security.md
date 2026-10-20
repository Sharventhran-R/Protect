# Security & Simulation Safety Rules

These rules establish strict security boundaries, secret hygiene, and physical safety constraints for the **Autonomous Agentic AI Home Guard** system.

---

## 1. Untrusted Input Invariant
- **External Data is Untrusted**: Treat all camera frames, RTSP video streams, sensor payloads, webhooks, and external network data as untrusted.
- **Strict Schema Validation**: Parse external inputs through validated schemas (e.g. dataclasses or Pydantic models) with bounded field lengths and type assertions before passing to downstream pipelines.
- **Path Sanitization**: Validate and resolve all file paths for video recordings or evidence exports to ensure no directory traversal (`../`) attacks can escape designated storage roots.

---

## 2. Secret Hygiene & Credentials
- **Zero Hardcoded Secrets**: Never commit or hardcode credentials, passwords, tokens, private keys, or API secrets.
- **Template-Only `.env.example`**: Maintain non-sensitive placeholders in `.env.example`.
- **Exclusion Verification**: Verify that `.env` and sensitive credential extensions (`*.pem`, `*.key`, `*.cert`) remain excluded by `.gitignore`.

---

## 3. LLM Reasoning Boundaries
- **Untrusted Model Output**: Outputs from local LLMs (Ollama) are probabilistic and untrusted. They must be validated against structured output schemas before consumption.
- **No Arbitrary Execution**: Never grant the LLM agent or workflow access to execute arbitrary shell commands, raw code strings, or unrestricted operating system calls.
- **Proposal-Only Outputs**: The LLM reasoning tier emits only `ActionProposal` recommendations—never direct execution commands.

---

## 4. Deterministic Action Authorization & Simulation
- **Deterministic Policy Safety Net**: All actions proposed by an agent must pass through an independent, deterministic policy engine before execution. If safety criteria (armed state, cooldown, threshold) are not met, the action is rejected.
- **Mandatory Simulation**: Physical hardware (alarms, spotlights, electronic locks) and emergency dispatches (police, fire) **MUST remain mocked** in simulation mode.
- **Never Disable Safety Checks**: Never bypass policy validators or mock guards to force tests or demos to pass.
