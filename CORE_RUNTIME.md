# CORE_RUNTIME.md

# SwitchBoard Core Runtime

> The SwitchBoard Core Runtime is the operating system of the SwitchBoard platform.
>
> It is responsible for orchestrating compute, understanding repositories, scheduling work,
> managing execution, remembering previous knowledge, and evaluating results.
>
> Everything built in SwitchBoard—whether a GitHub Issue Solver, Research Assistant,
> IDE Extension, CLI Tool, Browser Extension, or future applications—runs on top of this runtime.

---

# Philosophy

SwitchBoard is **not** an AI Agent Framework.

SwitchBoard is **not** a coding agent.

SwitchBoard is **not** a workflow builder.

Instead, SwitchBoard is a **local-first AI Compute Orchestration Platform**.

Applications define *what* should be done.

The Core Runtime determines *how* it should be executed.

The runtime is intentionally application-agnostic.

Its only responsibility is efficient execution.

---

# Runtime Architecture

```
                    Applications
                          │
                          ▼
                    SwitchBoard SDK
                          │
                          ▼
                        Kernel
                          │
 ┌─────────────┬──────────────┬──────────────┬──────────────┐
 ▼             ▼              ▼              ▼              ▼
Task      Execution      Context        Compute       Evaluation
System      Engine        Engine         Layer          Engine
   │             │              │             │             │
   └─────────────┴──────────────┴─────────────┘
                          │
                          ▼
                    Memory Engine
```

---

# Runtime Philosophy

Every subsystem follows the same design principles.

- Interface-first
- Pluggable implementations
- Event-driven communication
- Independent lifecycle
- Dependency injection
- Storage agnostic
- Backend agnostic
- Testable in isolation

The runtime is designed so that almost every component can be replaced without changing the rest of the platform.

---

# Core Subsystems

The runtime consists of seven major subsystems.

---

# 1. Kernel

## Responsibility

The Kernel is the central coordinator of the platform.

It owns the application lifecycle.

It does **not** execute AI workloads.

Instead, it initializes, starts, stops, and coordinates all runtime services.

---

## Responsibilities

- Bootstrap platform
- Load configuration
- Initialize services
- Shutdown services
- Maintain lifecycle state
- Host Event Bus
- Service registration

---

## Owns

- Service Registry
- Event Bus
- Configuration
- Bootstrap

---

## Never Responsible For

- Running models
- Scheduling tasks
- Repository parsing
- Memory retrieval

---

# 2. Compute Layer

## Responsibility

The Compute Layer abstracts model execution.

It provides a unified interface over different inference backends.

Applications never interact directly with Ollama, llama.cpp, vLLM, or future providers.

Instead they communicate only with the Compute Layer.

---

## Responsibilities

- Provider management
- Model loading
- Model unloading
- Streaming generation
- Session creation
- Interruptions
- Health monitoring

---

## Current Providers

- Mock Provider
- Ollama Provider

---

## Future Providers

- llama.cpp
- vLLM
- MLX
- OpenAI-compatible APIs
- TensorRT-LLM
- SGLang

---

## Design Principles

Provider implementations are replaceable.

SwitchBoard communicates through the IProvider interface only.

---

# 3. Context Engine

## Responsibility

The Context Engine understands repositories.

It performs deterministic repository analysis without using LLMs.

Its goal is to transform source code into structured knowledge.

---

## Responsibilities

- Repository scanning
- Language detection
- Gitignore filtering
- AST parsing
- Symbol extraction
- Dependency graph creation
- Context package generation
- Incremental cache invalidation

---

## Current Parser

- Python AST

---

## Future Parsers

- Tree-sitter
- JavaScript
- TypeScript
- Rust
- Go
- Java
- C++
- Kotlin
- Swift

---

## Output

The Context Engine produces ContextPackages that are consumed by Compute Layer during inference.

---

# 4. Task System

## Responsibility

The Task System defines work.

Every application converts user requests into Tasks.

Tasks are the fundamental execution unit inside SwitchBoard.

---

## Responsibilities

- Task lifecycle
- Task metadata
- Execution plans
- Dependency tracking
- Workflow DAG
- Artifact definitions

---

## Important Principle

Tasks describe work.

They never execute themselves.

---

# 5. Execution Engine

## Responsibility

The Execution Engine coordinates execution.

It transforms passive Tasks into actively running workloads.

---

## Responsibilities

- Queue management
- Scheduling
- Workflow traversal
- Resource allocation
- Retry policies
- Dispatch
- Execution coordination

---

## Scheduling Policies

Current:

- Sequential
- FIFO
- Priority + VRAM

Future:

- Deadline
- Adaptive
- Shortest Job First
- Reinforcement Learning
- Custom Plugins

---

## Important Principle

Execution Engine never generates tokens.

It delegates execution to the Compute Layer.

---

# 6. Memory Engine

## Responsibility

The Memory Engine stores reusable knowledge.

It enables SwitchBoard to improve over time.

Memory is execution-centric rather than conversation-centric.

---

## Types of Memory

Execution Memory

Stores execution history.

Context Memory

Stores repository knowledge.

Reflection Memory

Stores lessons learned.

Knowledge Memory

Stores reusable structured knowledge.

---

## Responsibilities

- Persistent storage
- Retrieval
- Ranking
- Archiving
- Reflection storage
- Memory lifecycle

---

## Current Stores

- InMemoryStore
- JSONFileStore

---

## Future Stores

- SQLite
- DuckDB
- PostgreSQL
- ChromaDB
- FAISS
- LanceDB
- Neo4j

---

# 7. Evaluation Engine

## Responsibility

The Evaluation Engine determines execution quality.

It closes the learning loop.

Evaluation produces structured feedback that becomes Memory.

---

## Responsibilities

- Metric calculation
- Report generation
- Recommendation generation
- Resource evaluation
- Artifact evaluation
- Workflow evaluation

---

## Current Evaluators

- Execution Evaluator
- Resource Evaluator
- Artifact Evaluator

---

## Future Evaluators

- LLM Judge
- Repository Evaluator
- Semantic Diff Evaluator
- Benchmark Evaluator
- Human Feedback Evaluator

---

# Runtime Communication

Every subsystem communicates through well-defined interfaces.

```
Task

↓

Execution Engine

↓

Context Engine

↓

Compute Layer

↓

Evaluation Engine

↓

Memory Engine
```

No subsystem should directly manipulate another subsystem's internal state.

Subsystems communicate through:

- Interfaces
- Events
- Shared Types

Never through implementation details.

---

# Event Driven Architecture

SwitchBoard follows an event-driven architecture.

Examples:

TaskCreated

↓

TaskQueued

↓

TaskStarted

↓

GenerationStarted

↓

GenerationCompleted

↓

EvaluationCompleted

↓

ReflectionStored

Events enable loose coupling between subsystems.

---

# Shared Runtime Principles

Every subsystem follows these principles.

## Interface First

Public behavior is defined through interfaces.

Implementations remain replaceable.

---

## Types First

All shared models live inside the `types` package.

Managers never own canonical data models.

---

## Pluggability

Major components must support interchangeable implementations.

Examples:

Compute Providers

Scheduling Policies

Memory Stores

Evaluators

Future Parsers

---

## Dependency Injection

Subsystems receive dependencies.

They never instantiate global implementations.

---

## Deterministic Core

Core runtime should never depend on LLM reasoning.

LLMs execute workloads.

They never define runtime behavior.

---

# Runtime Execution Flow

A typical execution proceeds as follows.

```
Application

↓

Create Workflow

↓

Create Tasks

↓

Execution Engine

↓

Resolve Ready Tasks

↓

Allocate Resources

↓

Build Context Package

↓

Create Compute Session

↓

Generate

↓

Evaluate Result

↓

Store Reflection

↓

Finish Workflow
```

---

# What the Runtime Does NOT Do

The runtime deliberately avoids application-specific logic.

It does not:

- Solve GitHub issues
- Write pull requests
- Review code
- Generate documentation
- Perform research
- Build websites

Those are responsibilities of applications built on top of SwitchBoard.

---

# Applications

Applications consume the runtime through the SwitchBoard SDK.

Examples include:

- GitHub Issue Solver
- Coding Assistant
- Research Assistant
- CLI Agent
- Browser Extension
- IDE Integration
- Multi-Agent Pipelines
- Autonomous Software Engineer

Applications remain thin.

The runtime provides all infrastructure.

---

# Future Evolution

The Core Runtime is intended to remain stable.

Future work should primarily occur through:

- New Compute Providers
- New Context Parsers
- New Scheduling Policies
- New Memory Stores
- New Evaluators
- New Applications
- Plugin SDK
- Ecosystem

The runtime itself should evolve slowly and conservatively.

---

# Vision

SwitchBoard aims to become the local operating system for AI execution.

Instead of repeatedly rebuilding orchestration logic for every new AI application, developers build once on top of the SwitchBoard Runtime.

The runtime manages compute, context, execution, memory, and evaluation.

Applications focus solely on solving user problems.

This separation allows SwitchBoard to remain reusable, extensible, and sustainable as AI systems continue to evolve.