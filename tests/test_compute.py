import pytest
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.registry.provider import ProviderRegistry
from switchboard.compute.adapters.mock import MockProvider
from switchboard.types.runtime import (
    GenerationRequest,
    ModelStatus,
    ModelCapability,
)
from switchboard.types.events import (
    ProviderLoadedEvent,
    SessionCreatedEvent,
    GenerationStartedEvent,
    GenerationCompletedEvent,
)
from switchboard.exceptions.base import RegistryError, SwitchBoardError

def test_provider_registry() -> None:
    registry = ProviderRegistry()
    provider = MockProvider()
    
    registry.register("mock", provider)
    assert registry.has("mock") is True
    assert registry.get("mock") is provider
    
    # Try duplicate registration
    with pytest.raises(RegistryError):
        registry.register("mock", provider)

    # Try lookup nonexistent
    with pytest.raises(RegistryError):
        registry.get("nonexistent")


@pytest.mark.asyncio
async def test_compute_manager_provider_loading() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    compute_manager = kernel.get_service("compute_manager")
    assert compute_manager is not None
    
    # Load mock provider
    await compute_manager.load_provider("mock")
    assert await compute_manager.health() is True
    
    # Verify models list
    models = await compute_manager.list_models()
    assert len(models) == 2
    assert {m.name for m in models} == {"mock-llama3", "mock-mistral"}
    
    # Verify capability list
    provider = await compute_manager.get_active_provider()
    caps = await provider.capabilities()
    assert ModelCapability.TEXT_GENERATION in caps
    
    # Unload provider
    await compute_manager.unload_provider()
    with pytest.raises(SwitchBoardError):
        await compute_manager.get_active_provider()

    await kernel.shutdown()


@pytest.mark.asyncio
async def test_compute_session_generation() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()

    event_bus = kernel.get_service("event_bus")
    compute_manager = kernel.get_service("compute_manager")
    await compute_manager.load_provider("mock")

    # Track fired events
    events = []
    async def log_event(event) -> None:
        events.append(event)

    await event_bus.subscribe(SessionCreatedEvent, log_event)
    await event_bus.subscribe(GenerationStartedEvent, log_event)
    await event_bus.subscribe(GenerationCompletedEvent, log_event)

    # Create session
    session = await compute_manager.create_session("mock-llama3")
    assert session.active_model == "mock-llama3"

    # Execute generation
    request = GenerationRequest(
        inputs={"prompt": "what is entropy?"},
        options={"temperature": 0.5}
    )
    response = await session.execute(request)
    
    assert "what is entropy?" in response.output
    assert response.finish_reason == "stop"
    assert response.provider == "mock"
    assert response.model == "mock-llama3"
    assert response.latency_ms > 0.0
    
    # Check history
    history = await session.get_history()
    assert len(history) == 1
    assert history[0]["request"]["inputs"]["prompt"] == "what is entropy?"
    
    # Check event bus logs
    event_types = [type(e) for e in events]
    assert SessionCreatedEvent in event_types
    assert GenerationStartedEvent in event_types
    assert GenerationCompletedEvent in event_types

    await kernel.shutdown()


@pytest.mark.asyncio
async def test_compute_session_streaming() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()

    compute_manager = kernel.get_service("compute_manager")
    await compute_manager.load_provider("mock")
    session = await compute_manager.create_session("mock-llama3")

    request = GenerationRequest(inputs={"prompt": "tell me a story"})
    stream_iter = await session.execute_stream(request)

    responses = []
    async for chunk in stream_iter:
        responses.append(chunk)

    assert len(responses) > 0
    # Final response chunk check
    assert responses[-1].finish_reason == "stop"
    assert "SwitchBoard Mock Provider" in responses[-1].output
    
    # History must record the final output
    history = await session.get_history()
    assert len(history) == 1
    assert "SwitchBoard Mock Provider" in history[0]["response"]["output"]

    await kernel.shutdown()


@pytest.mark.asyncio
async def test_compute_session_cancellation() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()

    compute_manager = kernel.get_service("compute_manager")
    await compute_manager.load_provider("mock")
    session = await compute_manager.create_session("mock-llama3")

    request = GenerationRequest(inputs={"prompt": "cancellation test"})
    stream_iter = await session.execute_stream(request)

    responses = []
    # Read one chunk and then trigger cancellation
    async for chunk in stream_iter:
        responses.append(chunk)
        await session.cancel()

    # The stream should have terminated early with finish_reason interrupted
    assert len(responses) < 13  # MockProvider normally sends 13 chunks
    assert responses[-1].finish_reason == "interrupted"

    await kernel.shutdown()
