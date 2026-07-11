# registry Subsystem

## Purpose
The `registry` subsystem manages the registration, retrieval, lifecycle, and dependency injection of all SwitchBoard platform components. It enables loose coupling by ensuring subsystems lookup dependencies dynamically rather than referencing static/global states.

## Responsibilities
- Implement the `ServiceRegistry` which handles registrations of instances implementing `IService`.
- Resolve dependencies between services using topological sorting to ensure correct initialization, start, and shutdown execution order.

## Public APIs
- `ServiceRegistry`: Concrete implementation of `IRegistry[IService]` with topological lifecycle sequencing.

## Future Work
- Add `ModelRegistry` for model management.
- Add `RuntimeRegistry` for inference adapters.
- Add `PluginRegistry` for discovering and listing plugin instances.
