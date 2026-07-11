import pytest
import pytest_asyncio
from switchboard.config.settings import Settings
from switchboard.registry.service import ServiceRegistry
from switchboard.kernel.event_bus import EventBus
from switchboard.kernel.resource_manager import ResourceManager

@pytest.fixture
def clean_settings() -> Settings:
    return Settings(
        env="test",
        log_level="DEBUG",
        max_vram_gb=10.0,
        max_ram_gb=16.0
    )

@pytest.fixture
def service_registry() -> ServiceRegistry:
    return ServiceRegistry()

@pytest_asyncio.fixture
async def event_bus() -> EventBus:
    bus = EventBus()
    await bus.initialize()
    await bus.start()
    yield bus
    await bus.shutdown()


@pytest.fixture(autouse=True)
def clean_memory_file() -> None:
    import os
    # Clean before test
    if os.path.exists(".switchboard/memory.json"):
        try:
            os.remove(".switchboard/memory.json")
        except Exception:
            pass
    yield
    # Clean after test
    if os.path.exists(".switchboard/memory.json"):
        try:
            os.remove(".switchboard/memory.json")
        except Exception:
            pass
