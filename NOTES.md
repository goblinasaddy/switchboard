# SwitchBoard Engineering Notes & Journal

## July 2026 — Phase 1 & 1.5 Architecture Validation

During Phase 1 (Compute Layer Design) and Phase 1.5 (Ollama Integration), we successfully validated the platform's core execution abstractions against a real-world inference backend.

### Key Learnings & Validations:

1. **Provider-Agnostic Abstraction (`IProvider`)**:
   - The separation between provider configuration and session state proved highly effective.
   - The contract successfully wraps model discovery (`list_models`), resource tracking (`estimated_vram_gb`), and lifecycle control without leaking Ollama-specific behaviors.

2. **Compute Sessions (`ComputeSession`)**:
   - Isolating prompt execution traces inside sessions provides an elegant boundary for streaming chunk assemblies, performance telemetry, and socket cancellations.
   - This shields the providers from state management (like conversational history or project context).

3. **Dynamic Model Lifecycle**:
   - We mapped on-demand memory management directly to Ollama using `/api/generate` with `keep_alive = -1` (loading) and `keep_alive = 0` (unloading).
   - This validates that resource-aware, VRAM-resident scheduling is fully supported by the architecture.

4. **Resource Footprint Heuristics**:
   - The parameter-size and quantization-level heuristic correctly estimated model VRAM footprints (e.g. `8B` models with 4-bit quantizations occupy ~5.5 GB VRAM), which will feed directly into the upcoming Scheduler subsystem.
