# SwitchBoard Design Decisions

> This document records important architectural decisions made throughout the development of SwitchBoard.
>
> The purpose of this file is to preserve the reasoning behind major design choices so that future development remains consistent with the project's vision.
>
> Every significant decision should answer:
>
> * What decision was made?
> * Why was it made?
> * What alternatives were considered?
> * What are the long-term consequences?

---

# Decision 001 — Build a Platform Instead of a Coding Agent

**Status:** Accepted

## Decision

SwitchBoard will be developed as a local-first AI compute orchestration platform rather than a standalone AI coding assistant.

## Reasoning

Most existing AI projects focus on solving one application (coding, research, writing, etc.).

SwitchBoard instead provides reusable compute orchestration infrastructure that allows multiple AI-powered applications to be built on top of the same coordination layer.

Applications become consumers of the platform instead of containing their own orchestration logic.

## Consequences

* Better modularity
* Easier future expansion
* Larger ecosystem potential
* Clear separation between platform and applications

---

# Decision 002 — Local-First Architecture

**Status:** Accepted

## Decision

SwitchBoard is designed primarily for local AI execution.

Cloud providers may be supported in the future through runtime adapters but are not part of the core architecture.

## Reasoning

The project aims to maximize software engineering capabilities on consumer hardware while minimizing dependency on paid APIs.

Local execution also provides privacy, lower long-term costs, and offline capability.

## Consequences

* Runtime abstraction becomes critical.
* Resource management becomes a first-class concern.
* Hardware-aware scheduling becomes part of the architecture.

---

# Decision 003 — Compute is a Managed Resource

**Status:** Accepted

## Decision

GPU memory, CPU, RAM, context, models, tools, and execution pipelines are treated as managed resources rather than static components.

## Reasoning

Traditional AI frameworks assume abundant compute resources.

SwitchBoard instead assumes constrained hardware and optimizes resource allocation throughout execution.

## Consequences

* Scheduler becomes a core subsystem.
* Dynamic model loading becomes possible.
* Future support for multiple GPUs and distributed execution is simplified.

---

# Decision 004 — Compute Layer Abstraction

**Status:** Accepted

## Decision

No subsystem communicates directly with Ollama, llama.cpp, vLLM, or any other inference backend.

All model execution, loading, and registration occur through the Compute Layer interface, using a dynamic Provider Registry and isolated Compute Sessions.

## Reasoning

This prevents vendor lock-in, abstracts model loading states (including VRAM residency), and provides clean session-oriented boundaries for history tracking and stream cancellations.

## Consequences

* Easier extensibility
* Cleaner testing
* Provider independence
* Session-isolated trace boundaries

---

# Decision 005 — Plugin-First Design

**Status:** Accepted

## Decision

Every major subsystem should be extensible through plugins whenever practical.

Examples include:

* Models
* Agents
* Context optimizers
* Evaluation modules
* Tool providers

## Reasoning

The long-term success of SwitchBoard depends on community contributions rather than a fixed implementation.

## Consequences

* Stable interfaces become essential.
* Plugin discovery becomes part of the Kernel.
* Documentation quality becomes more important.

---

# Decision 006 — Applications Should Be Thin

**Status:** Accepted

## Decision

Applications should describe desired outcomes rather than implementing orchestration logic.

The platform determines execution strategy.

## Reasoning

This prevents duplicated orchestration across applications and allows future improvements to benefit every application automatically.

## Consequences

* More reusable infrastructure
* Easier maintenance
* Consistent execution across applications

---

# Decision 007 — Context Engineering is a First-Class System

**Status:** Accepted

## Decision

Context processing is treated as an independent subsystem rather than helper utilities.

## Reasoning

Repository understanding is one of the largest bottlenecks for local AI systems.

Investing in context quality improves every downstream model.

## Consequences

* Dedicated Context Engine
* Plugin-based optimization
* Future support for advanced retrieval techniques

---

# Decision 008 — Engineering Memory Instead of Chat Memory

**Status:** Accepted

## Decision

Memory is designed around software engineering workflows rather than conversations.

Examples include:

* Repository knowledge
* Previous execution results
* Reflection outputs
* Architecture summaries
* Implementation history

## Reasoning

SwitchBoard is an engineering platform rather than a chatbot.

Persistent engineering knowledge provides greater long-term value than conversational history.

## Consequences

* Structured memory design
* Better repository understanding
* Reduced repeated computation

---

# Decision 009 — Event-Driven Internal Communication

**Status:** Accepted

## Decision

Subsystems should communicate using events rather than direct dependencies whenever practical.

## Reasoning

Loose coupling makes the platform easier to extend, test, and scale.

## Consequences

* Easier plugin integration
* Better observability
* Simpler future distributed execution

---

# Decision 010 — Build for Consumer Hardware First

**Status:** Accepted

## Decision

All architectural decisions should assume consumer-grade hardware as the primary deployment target.

Typical target systems include:

* 6 GB VRAM
* 8 GB VRAM
* 12 GB VRAM
* 16 GB VRAM

## Reasoning

The project's mission is to maximize AI capability on hardware commonly available to students, independent developers, and hobbyists.

## Consequences

* Efficient scheduling is prioritized over brute-force scaling.
* Memory efficiency becomes a core design goal.
* Future cloud support remains optional rather than required.

---

# Decision 011 — Research Follows Implementation

**Status:** Accepted

## Decision

The primary objective is to build a functional platform before pursuing academic publication.

## Reasoning

A working system provides stronger evidence than theoretical claims.

Research contributions should emerge naturally from implementation, experimentation, and benchmarking.

## Consequences

* Development is prioritized over paper writing.
* Evaluation infrastructure is planned early.
* Future publications will be backed by measurable results.

---

# Decision 012 — Session-Based Execution Flow

**Status:** Accepted

## Decision

Every generation/inference request is scoped within a `ComputeSession` instead of directly executing on a provider.

## Reasoning

Scoping generation inside sessions allows the platform to support features like conversation history, repository context caching, runtime execution memory, and cancel-safety directly at the session boundary. Providers remain thin and stateless, focusing solely on executing the raw model forward passes.

## Consequences

* Provides clean cancellation hooks (disconnecting active streams) without affecting other parallel generations.
* Keeps provider code stateless and simpler.
* Enables session-level telemetry (e.g. cumulative token usages and overall session latency).

---

# Future Decisions

The following topics remain open and will be revisited as development progresses.

* Programming language strategy beyond Python
* Multi-GPU scheduling
* Distributed execution
* Marketplace architecture
* Security and sandboxing
* Workflow definition language
* Remote runtime execution
* Model benchmarking framework
* Plugin packaging and distribution
* Licensing strategy
