# kernel Subsystem

## Purpose
The `kernel` subsystem is the core execution and orchestration heart of the SwitchBoard platform. It initializes, manages transitions of system states, owns resources, and hosts the platform's Event Bus communication backbone.

## Responsibilities
- Coordinate platform bootstrapping (`bootstrap.py`).
- Implement and manage the lifecycle states of the engine (`lifecycle.py`, `state.py`, `kernel.py`).
- Provide the asynchronous `EventBus` (`event_bus.py`) enabling decoupled, event-driven communication.
- Define the placeholder `ResourceManager` (`resource_manager.py`) to manage GPU memory, models, and tasks as schedulable units.

## Public APIs
- `Kernel`: Central engine coordinating service registries, config loading, and lifecycle state changes.
- `EventBus`: Concrete async implementation of `IEventBus` executing handler dispatches.
- `ResourceManager`: Coordinates allocations of GPU/VRAM/CPU resources.
- `KernelState`: Enum representing the current lifecycle phase (uninitialized, initializing, running, shutting_down, stopped, error).

## Future Work
- Add full VRAM scheduling logic within the `ResourceManager`.
- Add hot-reloading hooks for plugins.
- Implement telemetry logging inside the event loop for CPU/GPU profiling.
