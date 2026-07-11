# sdk Subsystem

## Purpose
The `sdk` subsystem provides a high-level programmatic interface for external applications (e.g. IDE extensions, autonomous agents, and CLI wrappers) to interact with the SwitchBoard runtime kernel.

## Responsibilities
- Provide a clean, easy-to-use client interface (`client.py`) to connect to and control a running SwitchBoard instance.
- Expose SDK commands matching the underlying kernel's capabilities (loading models, executing tasks, querying metrics).

## Public APIs
- `SwitchBoardClient`: High-level SDK client representation.

## Future Work
- Implement full REST/gRPC client communication to coordinate with a remote or daemonized SwitchBoard kernel.
- Add support for event-driven stream subscriptions through the SDK (e.g. streaming inference tokens or metrics).
