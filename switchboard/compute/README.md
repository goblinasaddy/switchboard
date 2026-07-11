# compute Subsystem (Compute Layer)

## Purpose
The `compute` subsystem implements the Compute Layer of SwitchBoard, functioning as the unified computation interface for all inference requests. It orchestrates model lifecycle requests (loading/unloading), registers third-party providers, and provisions isolated execution sessions.

## Responsibilities
- Coordinate connection hooks, loading, and selection of compute providers (Ollama, llama.cpp, etc.).
- Expose the centralized `ComputeManager` implementing `IComputeLayer` and coordinating provider interactions.
- Provision session contexts (`ComputeSession`) implementing `IComputeSession` to manage memory, cancellations, and generation sequences.

## Public APIs
- `ComputeManager`: Coordinator class providing session generation, model listings, and provider controls.
- `ComputeSession`: Handles request routing, cancellation tokens, and history.

## Future Work
- Add full support for multi-model loading and unloading within sessions.
- Implement token-level context caching at the session layer.
- Add remote inference provider adapters (e.g. OpenAI API, Anthropic API) for hybrid local/cloud workflows.
