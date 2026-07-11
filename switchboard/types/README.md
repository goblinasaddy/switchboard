# types Subsystem

## Purpose
The `types` subsystem serves as the single source of truth for all shared data types, validation schemas, and common enums in the SwitchBoard platform. It ensures consistent data representation across decoupled subsystems.

## Responsibilities
- Define shared validation structures using Pydantic.
- Define common type aliases and enums utilized by multiple packages.
- Implement the core `BaseEvent` class from which all system events derive.

## Public APIs
- `BaseEvent`: The foundational event model containing structural metadata (ID, timestamp, topic, payload).

## Future Work
- Add type definitions for resource allocation structures (CPU, GPU, VRAM specifications).
- Add schemas for model registry configurations and execution task tracking.
