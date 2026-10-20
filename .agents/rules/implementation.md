# Implementation Rules & Engineering Standards

These rules govern all code design, refactoring, and dependency management for the **Autonomous Agentic AI Home Guard** system.

---

## 1. Scope Control & Phase Discipline
- **Authorized Phase Only**: Implement only features belonging to the explicitly active phase in `AGENT_MEMORY.md`.
- **No Speculative Abstractions**: Solve current phase requirements directly. Do not build speculative frameworks or abstractions for unapproved future phases.
- **Inspect Callers Before Modifying**: Before changing shared functions, dataclasses, or protocols, inspect all callers and corresponding tests.

---

## 2. Code Quality & Modularity
- **Single-Purpose Units**: Functions and methods must be small, cohesive, and have a single clear responsibility.
- **Composition over Inheritance**: Favor explicit composition and dependency injection over deep class hierarchies or module-level singletons.
- **No Global Mutable State**: Keep state encapsulated within runtime instances. Avoid module-level mutable lists, dicts, or global flags.
- **Framework Independence**: Pure domain logic and data structures must remain independent of specific external frameworks (e.g. FastAPI, OpenCV, LangGraph) wherever practical.

---

## 3. Strict Static Typing
- **Comprehensive Signatures**: All public functions, methods, class attributes, and return types must have explicit type annotations.
- **No Broad `Any`**: Do not use `typing.Any` or unconstrained casts (`cast(Any, ...)`) to bypass type checker warnings. Use typed protocols, generics, or union types.
- **Immutable Data Transfer**: Use `@dataclass(frozen=True)` or Pydantic `frozen=True` models for inter-module event objects and messages to prevent unintended mutation.

---

## 4. Dependency Discipline
- **pyproject.toml as Source of Truth**: All project and development dependencies must be declared in `pyproject.toml`.
- **Minimal Dependencies**: Do not add runtime dependencies for functionality that standard library modules (`dataclasses`, `asyncio`, `json`, `datetime`) can cleanly handle.
- **Reproducible & Isolated**: Install dependencies strictly within the repository `.venv` using `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`. Never install packages globally.
