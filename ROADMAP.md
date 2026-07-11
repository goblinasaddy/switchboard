# SwitchBoard Roadmap

> **Version:** v0.1
> **Status:** Active
> **Last Updated:** July 2026

---

# Vision

SwitchBoard aims to become the foundational runtime platform for local AI systems.

Rather than being a single AI application, SwitchBoard seeks to provide the infrastructure that powers intelligent, resource-aware AI applications across multiple domains.

The roadmap below outlines the long-term direction of the platform.

---

# Long-Term Roadmap

The platform evolution is divided into structured phases. Each phase builds upon the previous one to deliver an increasingly capable, resource-aware, and community-driven orchestration system.

## Phase 0 — Foundation ✅

**Objective:** Create the platform skeleton.
* Dynamic Service Registry for dependency management.
* High-performance asynchronous Event Bus.
* Priority-based Configuration (TOML, Env, Overrides) and structured JSON logging.
* Interface skeleton, basic plugin manager, and interactive CLI.

---

## Phase 1 — Compute Layer ✅

**Objective:** Validate Compute Layer abstraction against a real inference backend.
* Decouple inference orchestration from specific backend providers (such as Ollama or llama.cpp).
* Implement provider-agnostic `IProvider`, `Model`, `GenerationRequest`, and `GenerationResponse` models.
* Create isolated `ComputeSession` traces to manage stream cancellation and execution history.
* Dynamic `ProviderRegistry` allowing decoupled auto-discovery of engines.
* Validated using a full `OllamaProvider` implementation.

---

## Phase 2 — Context Engine

**Objective:** Extract and index repository structure to minimize context windows.
* Scan directory structures and build symbol index tables.
* Use AST analysis to extract code relations and symbols.
* Construct code dependency graphs to support semantic lookups.
* Minimize prompt context footprints using pluggable context compression strategies.

---

## Phase 3 — Scheduler

**Objective:** Resource-aware scheduling of AI workloads on consumer-grade hardware.
* Dynamic VRAM scheduling (loading/unloading model weight files on-demand).
* Enforce model context limitations and memory priority queues.
* Target consumer setups (e.g. 6 GB, 8 GB, 12 GB, 16 GB VRAM configurations) dynamically.
* Implement task queues to isolate compute spikes and balance thread allocations.

---

## Phase 4 — Memory Engine

**Objective:** Retain and reuse engineering knowledge across executions.
* Store code semantics, structural graphs, and reflection outcomes.
* Enable cross-session memory lookup to prevent redundant LLM queries.
* Save execution templates and plan history for continuous optimization.

---

## Phase 5 — First End-to-End Workflow

**Objective:** Execute the first integrated software engineering task autonomously.
* Connect Context, Compute, and Tool layers to solve real bugs from issue descriptions.
* Deliver localized patches, verify changes through unit tests, and output complete review results.

---

## Phase 6 — Evaluation & Benchmarking

**Objective:** Record quality metrics, throughput latency, and cost factors.
* Benchmarking dashboards tracking latency, tokens-per-second, and VRAM efficiency.
* System evaluation loops to prevent performance regressions on local codebases.

---

## Phase 7 — Ecosystem Phase

**Objective:** Culmination of the platform as an open, community-driven registry.
* **Plugin SDK**: Standard protocols and guidelines for building plugins.
* **Marketplace**: Publish and share customized agents, tools, and optimizers.
* **Package Manager**: Install and update plugins seamlessly.
* **Community Registry**: Central database of approved community plugins.
* **Documentation Portal**: Interactive developer guides and references.
* **Version Compatibility**: Tools to check plugin/platform version compliance.
* **Developer Tooling**: CLI testing generators for plugin validation.

---

# Future Domains

Although SwitchBoard begins with software engineering, its architecture is intentionally domain-agnostic. Potential future applications include:

* Scientific research
* Robotics
* Cybersecurity
* Data engineering
* Autonomous agents
* Enterprise workflow automation

The platform should evolve through reusable infrastructure rather than domain-specific implementations.

---

# Guiding Principles

Every major release should improve at least one of the following:

* Performance
* Resource efficiency
* Extensibility
* Developer experience
* Reliability
* Maintainability

Growth should come from strengthening the platform rather than increasing complexity.

---

# What We Will Not Do

SwitchBoard will not pursue features that compromise its long-term architecture.

Examples include:

* Hardcoded model support
* Vendor-specific APIs
* Monolithic implementations
* Platform-specific assumptions
* Tight coupling between subsystems

Architectural consistency always takes priority over short-term convenience.

---

# Success Criteria

SwitchBoard will be considered successful if it achieves the following:

* Developers can build AI applications on top of the platform.
* Local AI workflows become significantly easier to orchestrate.
* Consumer hardware is utilized more efficiently.
* The community contributes plugins, models, and workflows.
* The architecture remains modular and maintainable as the project grows.

---

# Looking Ahead

SwitchBoard is envisioned as a long-term platform rather than a short-term project.

Each milestone should strengthen the underlying runtime, enabling future applications, research, and community contributions without requiring fundamental architectural redesign.
