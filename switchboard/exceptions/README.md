# exceptions Subsystem

## Purpose
The `exceptions` subsystem establishes a standardized hierarchy of errors for the SwitchBoard platform, replacing generic Python exceptions with domain-specific errors for easier debugging and structured handling.

## Responsibilities
- Define a root exception (`SwitchBoardError`) from which all custom platform errors inherit.
- Implement subsystem-specific errors to provide distinct error contexts.

## Public APIs
- `SwitchBoardError`: Base class for all exceptions raised by SwitchBoard.
- `KernelError`: Errors occurring within the central orchestrator or lifecycle management.
- `RegistryError`: Errors occurring during service registration or dependency resolution.
- `EventBusError`: Errors related to asynchronous event dispatching or handler registration.
- `PluginError`: Errors raised during plugin discovery, loading, or validation.
- `ConfigError`: Errors relating to parsing and loading settings.

## Future Work
- Expand exception definitions to include runtime-specific failures (e.g. `ModelLoadError`, `VRAMExhaustedError`, `InferenceTimeoutError`).
