# System Architecture & Component Boundaries

This document defines the architectural boundaries, interaction models, and safety guarantees for the **Autonomous Agentic AI Home Guard** system.

---

## 1. Architectural Overview & Boundaries

The architecture is partitioned into six decoupled subsystems:

```
[ Tier 1: Ingestion & Perception ]
  ├── Camera Feed Simulators (Synthetic Video Generator, Mock File Feeds)
  ├── Frame Ingestion Buffer (OpenCV, Timestamping, FPS Control)
  └── Object Detector (YOLO CPU Inference, Bounding Boxes, Classes)
             │
             ▼
[ Tier 2: Tracking & Behavior Analytics ]
  ├── Multi-Object Tracker (ByteTrack, Track IDs, Trajectory Vectors)
  ├── Feature Extraction (Velocity, Dwell Time, Zone Intersections)
  └── Behavior Classifier (Heuristic & Scikit-Learn Anomaly Classifiers)
             │
             ▼
[ Tier 3: Event Broker & Ingestion ]
  ├── Structured Security Event Publisher (Pydantic Event Schemas)
  └── Asynchronous In-Memory Queue / Event Bus
             │
             ▼
[ Tier 4: Agent Reasoning Engine ]
  ├── Incident Aggregator (Windowed Event Correlator)
  ├── LangGraph State Machine (Observation Gathering, Hypothesis Formation)
  └── Local LLM Reasoning (Ollama Contextual Analysis & Threat Scoring)
             │
             ▼
[ Tier 5: Deterministic Policy Validator (SAFETY GATE) ]
  ├── Armed State & Permission Checker
  ├── Rate Limiting & Cooldown Enforcer
  ├── Action Parameter & Escalation Ladder Verifier
  └── Audit Trail Recorder
             │
             ▼
[ Tier 6: Action Dispatch & Presentation ]
  ├── Simulated Actuators (Audible Chimes, Floodlights, Mocked Push Notifications)
  ├── Operator Incident Dashboard (FastAPI REST/WebSocket + React/Vite UI)
  └── Incident History & Video Evidence Storage
```

### Runtime Tier to Implementation Phase Mapping

| Architectural Subsystem | Primary Implementation Phase | Phase Scope Boundary |
| :--- | :--- | :--- |
| **Tier 1: Ingestion** | **Phase 1: Synthetic Camera & Frame Ingestion Engine** | Synthetic generator, file feeds, frame buffering (NO YOLO) |
| **Tier 1: Perception** | **Phase 2: Object Detection & Multi-Object Tracking** | CPU YOLO detector, bounding box generation |
| **Tier 2: Tracking** | **Phase 2: Object Detection & Multi-Object Tracking** | ByteTrack IDs, trajectory vectors, dwell time |
| **Tier 2: Behavior** | **Phase 3: Behavioral Classifier & Event Pipeline** | Heuristic & scikit-learn anomaly classifiers |
| **Tier 3: Event Broker** | **Phase 3: Behavioral Classifier & Event Pipeline** | Pydantic event schemas, async event bus |
| **Tier 4: Agent Reasoning** | **Phase 4: Agent Reasoning & Incident Synthesis** | LangGraph state loop, local Ollama LLM integration |
| **Tier 5: Policy Validator** | **Phase 5: Deterministic Policy Engine & Action Dispatch** | Deterministic safety gate, authorization rules |
| **Tier 6: Action & UI** | **Phase 5 (Actions) & Phase 6 (Dashboard)** | Mocked actuators, Vite/React incident dashboard |

---

## 2. Subsystem Responsibilities

### 2.1 Tier 1: Perception Subsystem
- **Boundary**: Ingests raw video frames (from local files or synthetic rendering) and emits detected bounding boxes with confidence scores.
- **Constraints**: Pure perception; holds no historical track identity or domain logic. Works on CPU.

### 2.2 Tier 2: Tracking & Behavior Analytics
- **Boundary**: Associates detections across frames into continuous tracks, assigns persistent track identifiers, and identifies spatial-temporal anomalies (e.g. loitering near an entry point for $>30$ seconds).
- **Constraints**: Emits discrete, immutable `SecurityEvent` objects.

### 2.3 Tier 3: Event Broker
- **Boundary**: Decouples the real-time frame processing loop from downstream asynchronous agent workflows.
- **Constraints**: Delivers events to consumer queues without dropping frames.

### 2.4 Tier 4: LangGraph Agent Reasoning
- **Boundary**: Synthesizes sequences of events into high-level `Incident` narratives using structured prompting against a local LLM via Ollama.
- **Constraints**: Probabilistic reasoning only. Output is strictly an `ActionProposal` payload—**never** an executable command.

### 2.5 Tier 5: Deterministic Policy Validator
- **Boundary**: The critical security boundary. Evaluates the agent's `ActionProposal` against rigid, deterministic policies.
- **Rules**:
  - If armed state is `DISARMED`, high-severity active interventions are rejected.
  - If action frequency exceeds threshold, actions are throttled.
  - If threat score does not meet minimum bar, escalation is denied.
- **Guarantees**: Zero probabilistic or non-deterministic code executes inside this gate.

### 2.6 Tier 6: Action Dispatch & Presentation
- **Boundary**: Executes authorized actions against simulated actuators and serves the operator web dashboard.
- **Constraints**: Physical devices and external authorities remain mocked in simulation.

---

## 3. Data Flow & Contract Schema

All intra-system communication occurs via strictly typed immutable data models:

1. `Frame`: `(timestamp_ns, frame_id, camera_id, image_bytes, resolution)`
2. `Detection`: `(track_id, label, confidence, bbox_coords)`
3. `SecurityEvent`: `(event_id, event_type, camera_id, timestamp, features, severity)`
4. `Incident`: `(incident_id, start_time, last_updated, correlated_events, status)`
5. `ActionProposal`: `(proposal_id, incident_id, proposed_action, parameters, rationale)`
6. `PolicyDecision`: `(is_authorized, authorized_action, rejection_reason, audit_token)`

---

## 4. Simulation Isolation Guarantee

To satisfy the non-goal of requiring physical hardware or cameras:
- All video sources read from synthetic generators or recorded MP4/AVI clips.
- All hardware controls invoke software mock handlers that log actions to an in-memory/sqlite audit trail.
- Tests never attempt external network connections or socket binds to real physical devices.
