# interfaces Subsystem

## Purpose
The `interfaces` subsystem defines the abstract contracts and protocol definitions for all major SwitchBoard modules. It serves as the decouple point to guarantee that subsystems never directly depend on concrete implementations, enforcing the "Everything is Replaceable" design philosophy.

## Responsibilities
- Define structural and runtime contracts via Python `typing.Protocol` or `abc.ABCMeta`.
- Enforce standard interfaces for lifecycle management (`IService`), event propagation (`IEventBus`), service lookup (`IRegistry`), and runtime execution.
- Maintain a clean boundary where no domain logic or concrete dependency imports exist.

## Public APIs
- `IService`: Lifecycle protocol defining initialization, startup, and shutdown hooks.
- `IEventBus`: Protocol for asynchronous event subscriptions and publishing.
- `IRegistry`: Base interface for registration components.

## Future Work
- Add `IRuntime` interface for model runtime adapters (Ollama, llama.cpp).
- Add `IScheduler` interface for task scheduling.
- Add `IContextEngine` and `IMemoryEngine` interfaces for context manipulation and persistent state management.
