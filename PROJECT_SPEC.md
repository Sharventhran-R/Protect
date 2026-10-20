# PROJECT_SPEC.md — Master Architectural Specification
## Autonomous Agentic AI Home Guard (`Protect`)

---

## 1. Project Objectives & Non-Goals

### 1.1 Objectives
- Build an autonomous, agentic artificial intelligence home-security system capable of reasoning over visual perception streams, detecting anomalous and threatening behaviors, correlating observations into structured security incidents, and autonomously recommending or executing safety actions.
- **Simulation-First Engineering**: Provide an entirely self-contained software simulation environment where video feeds, environmental sensors, alarms, and emergency dispatches are modeled and verified without physical hardware or cameras.
- **CPU-First Execution**: Ensure all baseline pipelines (perception, tracking, classification, local LLM reasoning) execute cleanly on standard developer workstations without requiring dedicated GPU acceleration.
- **Safety by Construction**: Implement strict deterministic policy gates separating probabilistic agent reasoning from physical or external action authorization.

### 1.2 Non-Goals
- Real physical hardware integration in initial phases (no requirement for physical RTSP IP cameras, Zigbee/Z-Wave hubs, or smart door locks).
- Real 911/emergency authority dispatches (all dispatches are strictly simulated and logged).
- Heavyweight multi-GPU video analytics pipelines.
- Replacing certified professional home monitoring services without human verification.

---

## 2. High-Level Architecture & End-to-End Data Flow

The system processes continuous visual observations and transforms them through sequential abstraction layers:

```
[ Synthetic / Recorded Camera Feeds ]
                 │
                 ▼
[ Perception Engine (OpenCV / Frame Ingestion) ]  (PLANNED)
                 │
                 ▼
[ Object Detection & Tracking (YOLO / ByteTrack) ]  (PLANNED)
                 │
                 ▼
[ Feature Extraction & Behavioral Classifier ]  (PLANNED)
                 │
                 ▼
[ Structured Security Event Stream ]  (PLANNED)
                 │
                 ▼
[ Event Infrastructure (Async Queue / Redis / Kafka) ]  (PLANNED)
                 │
                 ▼
[ Agent Reasoning Workflow (LangGraph + Local LLM) ]  (PLANNED)
                 │
                 ▼
[ Deterministic Security Policy Validator ]  (PLANNED)
                 │
                 ▼
[ Simulated Action Dispatcher & Audit Log ]  (PLANNED)
                 │
                 ▼
[ Incident History & Monitoring Dashboard ]  (PLANNED)
```

### Component Implementation Status Matrix

| Component | Architecture Role | Target Phase | Status |
| :--- | :--- | :--- | :--- |
| **Foundation & Health** | Package bootstrap, health check, developer tooling | Phase 0: Engineering Foundation & Agent Guardrails | **IMPLEMENTED** |
| **Synthetic Feeds** | Camera simulation, video ingestion, mock RTSP/files | Phase 1: Synthetic Camera & Frame Ingestion Engine | Planned |
| **Perception Engine** | Frame pre-processing, object detection (YOLO) | Phase 2: Object Detection & Multi-Object Tracking | Planned |
| **Object Tracking** | Multi-object tracking (ByteTrack), trajectory analysis | Phase 2: Object Detection & Multi-Object Tracking | Planned |
| **Behavior Classifier** | Loitering, perimeter breach, forced entry classification | Phase 3: Behavioral Classifier & Event Pipeline | Planned |
| **Event Pipeline** | Asynchronous event broker, structured schemas | Phase 3: Behavioral Classifier & Event Pipeline | Planned |
| **LangGraph Agent** | Contextual multi-step reasoning, incident correlation | Phase 4: Agent Reasoning & Incident Synthesis | Planned |
| **Local LLM Engine** | Ollama integration (Qwen2.5 / Llama 3.2 lightweight) | Phase 4: Agent Reasoning & Incident Synthesis | Planned |
| **Policy Engine** | Deterministic rule-based action authorization gate | Phase 5: Deterministic Policy Engine & Action Dispatch | Planned |
| **Action Dispatcher** | Mocked actuator triggers, sound alarms, notifications | Phase 5: Deterministic Policy Engine & Action Dispatch | Planned |
| **Operator Dashboard** | Real-time web UI (Vite, React, Tailwind CSS) | Phase 6: Operator Dashboard & Incident Playback | Planned |
| **Observability** | Metrics, telemetry, incident audit replay | Phase 7: System Hardening & Observability | Planned |

---

## 3. Core Domain Concepts & Information Model

1. **Camera**: A physical or virtual optical sensor defined by its location, field of view, resolution, and operational schedule (e.g. `front_porch`, `driveway`, `backyard_gate`).
2. **Observation**: A single detection instance extracted from a frame (bounding box, label, confidence, timestamp).
3. **Track**: An active object identity maintained across consecutive frames with trajectory vectors, velocity, and dwell time.
4. **Security Event**: An anomalous or notable occurrence emitted when tracking features satisfy behavioral triggers (e.g., `PersonLoiteringEvent`, `PerimeterCrossedEvent`, `PackageUnattendedEvent`).
5. **Incident**: An aggregated, stateful security episode comprising multiple correlated events occurring within a spatial and temporal window.
6. **Threat Assessment**: The structured output of the LLM reasoning agent evaluating intent, urgency, severity score (1–10), and justification.
7. **Action**: A discrete operational intervention proposed by the agent (e.g., `ActivateFloodlight`, `SoundChime`, `SendMobilePushAlert`, `SimulatePoliceDispatch`).
8. **Scenario**: A scripted synthetic simulation run (e.g., package delivery, unauthorized night prowler, family member returning home) used for deterministic regression testing.

---

## 4. Planned Technology Stack & Rationale

- **Python (3.12+ target, running 3.14 on host)**: Core runtime combining rich scientific, CV, and agent ecosystems.
- **FastAPI, Pydantic & Asyncio (Phase 3+)**: High-performance, asynchronous REST/WebSocket server for streaming events and configuration.
- **OpenCV (Phase 1–2)**: Image transformations, video decoders, frame annotation, and motion detection.
- **YOLO & ByteTrack (Phase 2)**: Lightweight CPU-friendly object detection and robust multi-object tracking.
- **Scikit-Learn (Phase 3)**: Lightweight feature extraction and behavioral anomaly classification without GPU overhead.
- **LangGraph & Ollama (Phase 4)**: Stateful agent loop orchestrating complex multi-camera incident synthesis and local privacy-preserving LLM inference.
- **PostgreSQL & Redis (Phase 5+)**: Persistent incident storage, relational audit logs, and low-latency state caching.
- **React, TypeScript, Vite & Tailwind CSS (Phase 6)**: Responsive modern web dashboard for incident review, video playback, and simulation control.
- **Pytest, Ruff & Mypy**: Automated test harness, high-speed linting/formatting, and strict static type verification.

---

## 5. Security, Privacy & Safe-Action Invariants

1. **Local-Only Processing**: No video feeds, frames, or visual embeddings are transmitted to third-party cloud services. LLM reasoning runs entirely locally via Ollama.
2. **Deterministic Action Policy Guard**: The LLM agent **CANNOT** directly invoke external actions or simulated actuators. All proposed actions are evaluated by a deterministic policy engine that checks:
   - Operating hours and armed state.
   - Confidence threshold minimums.
   - Rate limiting and cooldown periods.
   - Escalation ladder constraints.
3. **Mock-Only Actuators**: Physical dispatches and emergency sirens remain simulated in software test harnesses by default.
4. **Secret Hygiene**: All configurations are externalized via environment variables. Zero credentials are committed to version control.
5. **Data Retention & Privacy Masking**: Visual evidence and frame captures must be stored in designated directory trees excluded from Git, with configurable automated retention and deletion policies.
