# SwitchBoard Architecture

> **Version:** v0.2
> **Status:** Active Design
> **Last Updated:** July 2026

---

# Overview

SwitchBoard is a **local-first AI compute orchestration platform** designed to orchestrate local AI workloads on consumer hardware. While software engineering is the platform's first target application, the architecture is designed as a general-purpose local AI compute orchestrator.

Unlike traditional AI systems that assume unlimited cloud compute or rely on single general-purpose models, SwitchBoard treats AI execution as a systems problem. It dynamically manages GPU memory, context, tools, and execution sessions to maximize performance and efficiency under constrained physical resources.

SwitchBoard does **not** replace the operating system or the inference engines. Instead, it functions as an AI compute orchestration layer that sits above local inference backends (such as Ollama, llama.cpp, or vLLM) and below thin, AI-powered applications.

Its primary objective is to provide a provider-agnostic, extensible platform capable of running resource-aware workflows while efficiently scheduling consumer-grade hardware.

---

# Design Philosophy

SwitchBoard is built around several core principles.

## Everything is a Resource

Every component inside SwitchBoard is considered a managed resource.

Examples include:

* Models
* VRAM
* CPU
* RAM
* Context
* Memory
* Tools
* Agents
* Tasks
* Pipelines

Resources are owned and managed by the platform rather than individual applications.

---

## Everything is Replaceable

No subsystem should depend on a specific implementation.

Examples include:

* Compute providers
* Models
* Context optimization methods
* Agents
* Tool providers

Every major component should be replaceable without requiring architectural changes.

---

## Compute is Schedulable

SwitchBoard treats computational resources similarly to how an operating system schedules CPU time.

Instead of permanently allocating GPU memory to one model, models are loaded, executed, and unloaded dynamically according to workflow requirements.

The scheduler is responsible for determining how available resources are utilized throughout execution.

---

## Applications Are Thin

Applications should contain minimal AI logic.

Their responsibility is to describe *what* should be accomplished.

SwitchBoard determines *how* the task is executed.

This separation allows multiple applications to share the same runtime platform.

---

# High-Level Architecture

```text
Applications
│
├── Coding IDE
├── CLI
├── Research Assistant
├── Browser Extension
└── Future Applications

────────────────────────────────────────────

SwitchBoard SDK

────────────────────────────────────────────

Kernel

├── Scheduler
├── Compute Layer
├── Context Engine
├── Memory Engine
├── Plugin Engine
└── Evaluation Engine

────────────────────────────────────────────

Compute Providers

├── Ollama
├── llama.cpp
├── vLLM
├── MLX
└── OpenAI-compatible APIs

────────────────────────────────────────────

Hardware

├── CUDA
├── ROCm
├── Metal
└── CPU

────────────────────────────────────────────

Operating System

├── Windows
├── Linux
└── macOS
```

---

# Core Components

## Kernel

The Kernel is the central coordinator of the platform.

It owns the lifecycle of every subsystem and acts as the communication hub for SwitchBoard.

Responsibilities include:

* Service orchestration
* Lifecycle management
* Resource ownership
* Event routing
* Dependency management

No subsystem communicates directly with another without passing through the platform's coordination mechanisms.

---

## Scheduler

The Scheduler is responsible for allocating resources throughout task execution.

Its responsibilities include:

* Task scheduling
* Agent scheduling
* Model scheduling
* VRAM scheduling
* Tool scheduling

The scheduler continuously determines which resources should be active and when.

---

## Compute Layer

The Compute Layer provides a unified, provider-agnostic abstraction for executing local AI workloads.

Instead of subsystems directly invoking inference backends (like Ollama, llama.cpp, or vLLM), the platform coordinates executions through isolated Compute Sessions. All providers register dynamically with a Provider Registry rather than being instantiated directly by the Compute Layer.

Responsibilities include:

* Provider registration and discovery (via the Provider Registry)
* Model lifecycle orchestration (loading and unloading models to/from VRAM)
* Isolated execution scoping (via Compute Sessions)
* Generation tracking (capturing token usage, latency, and cancel-safety)
* Provider-specific error translation (mapping provider errors to SwitchBoard errors)

---

## Context Engine

The Context Engine is responsible for transforming large repositories into structured, task-specific information.

Instead of repeatedly sending entire repositories to models, the Context Engine constructs compact context packages tailored to each stage of execution.

Responsibilities include:

* Repository indexing
* Symbol extraction
* Dependency analysis
* Context construction
* Context optimization
* Repository understanding

The Context Engine is designed to support pluggable optimization strategies.

---

## Memory Engine

The Memory Engine stores structured knowledge generated during execution.

Unlike conversational memory, SwitchBoard's memory system focuses on engineering knowledge.

Examples include:

* Repository understanding
* Execution history
* Reflection results
* Generated implementation plans
* Previous task outcomes

Memory allows future stages to reuse existing knowledge without repeating computation.

---

## Plugin Engine

The Plugin Engine enables SwitchBoard to remain modular.

Future extensions should be installable without modifying the platform itself.

Examples include:

* Agent plugins
* Model providers
* Context optimizers
* Tool providers
* Evaluation modules
* Workflow extensions

The Plugin Engine serves as the foundation of the future SwitchBoard ecosystem.

---

## Evaluation Engine

The Evaluation Engine measures execution quality.

Rather than simply producing outputs, SwitchBoard continuously records execution metrics that can be used for benchmarking, optimization, and future learning.

Possible metrics include:

* Execution time
* VRAM usage
* Memory consumption
* Token usage
* Iteration count
* Tool usage
* Success rate
* Failure reasons

---

# Data Flow

A typical execution follows the sequence below:

```text
User Task
        │
        ▼
Application
        │
        ▼
SwitchBoard SDK
        │
        ▼
Kernel
        │
        ▼
Scheduler
        │
        ▼
Context Engine
        │
        ▼
Compute Session
        │
        ▼
Compute Layer
        │
        ▼
Model Execution
        │
        ▼
Evaluation
        │
        ▼
Result
```

Each subsystem contributes to the execution while remaining independently replaceable.

---

# Extensibility

SwitchBoard is designed as a platform rather than a single application.

Future extensions may include:

* Multi-GPU execution
* Distributed execution
* Remote compute providers
* Additional model providers
* IDE integrations
* Marketplace for plugins
* Custom workflow definitions
* Specialized engineering agents
* Organization-level deployments

The architecture should evolve through extension rather than modification.

---

# Scope

The initial scope of SwitchBoard is focused on software engineering workflows executed using local AI models. However, the platform is architecturally designed as a general-purpose local AI compute orchestration engine capable of hosting any category of local model workloads.

---

# Long-Term Vision

SwitchBoard aims to become a foundational local AI compute orchestration platform.

Rather than building a single AI coding assistant, the project seeks to provide the infrastructure upon which many AI-powered applications can be developed.

Its long-term goal is to enable intelligent orchestration of models, sessions, context, memory, tools, and compute resources while remaining modular, extensible, and accessible to developers running on consumer hardware. This culminates in a robust Ecosystem including a package manager, plugin registry, and community marketplace.
