# SwitchBoard Development Plan

> **Version:** v0.2
> **Status:** Active Sprint
> **Current Milestone:** Context Engine

---

# Mission

The objective of the current development phase is **not** to build the best AI coding assistant.

The objective is to build the **local AI compute orchestration platform** that every future SwitchBoard application will depend on.

Every implementation decision should strengthen the platform rather than solving a single use case.

---

# Current Goal

Build the Context Engine milestone, moving from raw local compute execution to structured repository indexing and semantic representation.

By the end of this milestone, SwitchBoard should be able to:

* Parse a codebase's symbol tree (using AST analysis).
* Map symbol dependencies to construct a structured code-graph.
* Expose context optimization utilities to build compressed prompts.
* Serve code context packages dynamically to the Compute Layer.

No advanced scheduling or agent coordination is expected during this phase.

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

## Phase 2 — Context Engine

### Goal

Improve codebase repository indexing and AST parsing to feed optimized context packages to the Compute Layer.

---

### Deliverables

* Repository scanner and indexer
* Symbol extractor (AST structure parsing)
* Dependency parsing graph (code symbol relations)
* Context construction strategies
* Context packages output structures
* Stable Context Engine interfaces

---

### Completion Criteria

This phase is complete when:

* We can scan a local directory and extract structured symbol nodes.
* A symbol dependency graph can be built programmatically.
* The system constructs a minimized prompt context block based on user task targets.
* All Context Engine functionality is covered by automated unit tests.

---

# Completed Milestones

## Phase 0 — Foundation ✅

* Skeleton repository configuration and Pydantic-based settings.
* Topologically sorted Service Registry managing subsystem lifecycles.
* Async event bus, structured logging, and interactive CLI.

## Phase 1 — Compute Layer ✅

* Created provider-agnostic abstractions (`IComputeLayer`, `IComputeSession`, `IProvider`).
* Implemented isolated `ComputeSession` scopes representing prompt transaction boundaries.
* Created canonical data types (`Model`, `GenerationRequest`, `GenerationResponse`).
* Validated the architecture against a real backend using `OllamaProvider` (supporting model loading/unloading, text generation, chunk streaming, and socket closing interrupts).

---

# Future Milestones

## Phase 3 — Scheduler

Focus:

Enable resource-aware orchestration of tasks, agents, and models.

Expected features:

* Dynamic VRAM-aware model loading and unloading
* Task queuing and concurrency limits
* GPU and memory pressure monitors
* Multi-model sequencing schedules

---

## Phase 4 — Memory Engine

Focus:

Store structured engineering knowledge generated across executions.

Expected features:

* Repository representation memory
* Task reflection storage
* Plan templates and historical outcomes
* Cache reuse across separate agent pipelines

---

## Phase 5 — First End-to-End Workflow

Focus:

Validate the entire platform using a real software engineering agent pipeline.

Target workflow:

```text
GitHub Repository
       │
       ▼
Issue / Bug Report
       │
       ▼
Context Extraction & Planning
       │
       ▼
Model Execution & Coding
       │
       ▼
Verification & Verification
       │
       ▼
Pull Request / Patch Output
```

---

## Phase 6 — Evaluation & Benchmarking

Focus:

Establish structured quality, speed, and resource metrics.

Expected features:

* Benchmark suites for local code execution
* Latency and token throughput dashboards
* Accuracy regression tracking

---

## Phase 7 — Ecosystem

Focus:

Enable plugin development, distribution, and community participation.

Expected features:

* Plugin SDK and API rules
* Custom plugin package manager
* Community registry portal
* Sandbox runtime environments

---

# Current Priorities

Priority order for development:

1. Stable architecture ✅
2. Core platform ✅
3. Compute Layer ✅
4. Context Engine
5. Scheduler
6. Memory Engine
7. Evaluation & Benchmarking
8. Ecosystem & Marketplace
9. Thin Applications / Workflows

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
