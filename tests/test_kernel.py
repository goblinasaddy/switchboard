import pytest
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.kernel.state import KernelState
from switchboard.kernel.lifecycle import LifecycleEvent, ServiceLifecycleEvent
from switchboard.exceptions.base import KernelError

@pytest.mark.asyncio
async def test_kernel_bootstrap_lifecycle() -> None:
    # 1. Bootstrap Kernel
    overrides = {
        "env": "test",
        "log_level": "DEBUG",
        "max_vram_gb": 16.0
    }
    kernel = await bootstrap_platform(overrides=overrides)
    assert kernel.state == KernelState.UNINITIALIZED
    assert kernel.settings.env == "test"
    assert kernel.settings.max_vram_gb == 16.0

    # Retrieve Event Bus
    event_bus = kernel.get_service("event_bus")
    assert event_bus is not None

    # Track lifecycle events
    lifecycle_events = []
    service_events = []

    async def log_lifecycle(event: LifecycleEvent) -> None:
        lifecycle_events.append(event)

    async def log_service(event: ServiceLifecycleEvent) -> None:
        service_events.append(event)

    await event_bus.subscribe(LifecycleEvent, log_lifecycle)
    await event_bus.subscribe(ServiceLifecycleEvent, log_service)

    # 2. Initialize
    await kernel.initialize()
    assert kernel.state == KernelState.INITIALIZING
    
    # 3. Start
    await kernel.start()
    assert kernel.state == KernelState.RUNNING

    # 4. Shutdown
    await kernel.shutdown()
    assert kernel.state == KernelState.STOPPED

    # Validate lifecycle logs
    # Transitions should be: UNINITIALIZED -> INITIALIZING -> RUNNING -> SHUTTING_DOWN -> STOPPED
    states = [e.to_state for e in lifecycle_events]
    assert KernelState.INITIALIZING in states
    assert KernelState.RUNNING in states
    assert KernelState.SHUTTING_DOWN in states
    assert KernelState.STOPPED in states

    # Validate service lifecycle checks
    # ResourceManager and EventBus should have transitions
    services_initialized = [e.service_name for e in service_events if e.action == "initialize"]
    assert "resource_manager" in services_initialized


@pytest.mark.asyncio
async def test_kernel_invalid_transitions() -> None:
    kernel = await bootstrap_platform()
    # Cannot start without initializing first
    with pytest.raises(KernelError):
        await kernel.start()
