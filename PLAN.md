# SwitchBoard Development Plan

> **Version:** v0.1
> **Status:** Active Sprint
> **Current Milestone:** Foundation

---

# Mission

The objective of the current development phase is **not** to build the best AI coding assistant.

The objective is to build the **core runtime platform** that every future SwitchBoard application will depend on.

Every implementation decision should strengthen the platform rather than solving a single use case.

---

# Current Goal

Build the minimum foundation required for SwitchBoard to execute a complete AI workflow.

By the end of this milestone, SwitchBoard should be able to:

* Start the platform
* Load a local model
* Execute a simple task
* Manage execution through the Kernel
* Expose a stable CLI
* Support future subsystem integration

No advanced AI capabilities are expected during this phase.

---

# Development Philosophy

The project follows several engineering principles.

## Build Vertically

Instead of building every subsystem independently, complete one end-to-end workflow before adding advanced features.

A working system is always more valuable than many unfinished modules.

---

## Build for Extensibility

Whenever possible, build interfaces instead of implementations.

Future contributors should be able to extend SwitchBoard without modifying existing components.

---

## Avoid Premature Optimization

Focus on correctness, architecture, and clean interfaces.

Performance optimization comes only after a stable system exists.

---

## Keep Components Independent

Subsystems should remain loosely coupled.

Every module should have a clearly defined responsibility.

---

# Current Milestone

## Phase 0 — Foundation

### Goal

Create the architectural skeleton of SwitchBoard.

---

### Deliverables

* Repository structure
* Development environment
* CLI entry point
* Configuration system
* Logging system
* Service registry
* Event bus
* Basic plugin discovery
* Documentation

---

### Completion Criteria

This phase is complete when:

* SwitchBoard starts successfully.
* All core services initialize correctly.
* The CLI can execute a simple command.
* Plugin discovery functions correctly.
* Logging and configuration systems are operational.

No AI functionality is required.

---

# Future Milestones

## Phase 1 — Runtime

Focus:

Create a unified interface for local model execution.

Expected features:

* Runtime abstraction
* Ollama adapter
* Model registry
* Model loading
* Model unloading
* Health monitoring

---

## Phase 2 — Kernel & Scheduling

Focus:

Enable intelligent orchestration.

Expected features:

* Task scheduler
* Agent scheduler
* Resource management
* Sequential execution
* Initial VRAM scheduling

---

## Phase 3 — Context Engine

Focus:

Improve repository understanding.

Expected features:

* Repository indexing
* Tree-sitter integration
* Symbol extraction
* Dependency graph
* Context packages

---

## Phase 4 — First End-to-End Workflow

Focus:

Validate the platform.

Target workflow:

```text
GitHub Repository

↓

Issue

↓

Planning

↓

Implementation

↓

Review

↓

Output
```

At this point SwitchBoard becomes a usable application.

---

## Phase 5 — Optimization

Focus:

Improve execution quality.

Possible additions:

* Context compression
* Retrieval optimization
* Memory system
* Reflection
* Better scheduling
* Evaluation improvements

---

# Current Priorities

Priority order for development:

1. Stable architecture
2. Core platform
3. Runtime execution
4. Scheduling
5. Context Engine
6. Memory
7. Evaluation
8. Applications
9. Performance optimization

---

# Definition of Success

The first public milestone will be considered successful if a developer can:

1. Install SwitchBoard.
2. Connect a local model.
3. Analyze a repository.
4. Execute a simple AI workflow.
5. Receive a meaningful engineering result.

Everything beyond this milestone builds upon that foundation.

---

# Out of Scope

The following items are intentionally excluded from the current milestone:

* Multi-GPU execution
* Distributed execution
* Cloud orchestration
* Marketplace
* GUI application
* VS Code extension
* Research publication
* Advanced benchmarking
* Automatic model routing
* Workflow marketplace

These features will be considered only after the core platform has matured.

---

# Guiding Principle

Every completed milestone should leave the repository in a usable state.

At no point should the project become a collection of partially implemented ideas.

Each phase must produce a working, testable, and extensible foundation for the next stage of development.
