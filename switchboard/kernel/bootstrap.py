from typing import Any
from switchboard.config.loader import load_config
from switchboard.logging.config import configure_logging, get_logger
from switchboard.registry.service import ServiceRegistry
from switchboard.kernel.event_bus import EventBus
from switchboard.kernel.resource_manager import ResourceManager
from switchboard.kernel.kernel import Kernel

logger = get_logger("bootstrap")

async def bootstrap_platform(
    config_path: str | None = None,
    overrides: dict[str, Any] | None = None
) -> Kernel:
    """
    Bootstrap the SwitchBoard platform, creating the kernel, configuration settings,
    logging environment, and registering core services.
    
    Args:
        config_path: Optional path to a settings.toml file.
        overrides: Optional key-value dictionary of configuration overrides.
        
    Returns:
        An uninitialized Kernel instance with pre-registered services.
    """
    # 1. Load configuration setting rules
    settings = load_config(config_path, overrides)

    # 2. Configure structured tracing loggers
    configure_logging(settings.log_level)
    logger.info("Bootstrapping SwitchBoard platform...")

    # 3. Instantiate the Dependency Service Registry
    registry = ServiceRegistry()

    # 4. Instantiate & Register EventBus (backbone system-wide communication)
    event_bus = EventBus()
    registry.register("event_bus", event_bus)

    # 5. Instantiate & Register ResourceManager (manages VRAM, RAM, CPU threads)
    resource_manager = ResourceManager(
        max_vram_gb=settings.max_vram_gb,
        max_ram_gb=settings.max_ram_gb
    )
    registry.register("resource_manager", resource_manager)

    # 6. Instantiate & Register Compute Layer (ComputeManager + ProviderRegistry)
    from switchboard.registry.provider import ProviderRegistry
    from switchboard.compute.adapters.mock import MockProvider
    from switchboard.compute.adapters.ollama import OllamaProvider
    from switchboard.compute.manager import ComputeManager

    provider_registry = ProviderRegistry()
    provider_registry.register("mock", MockProvider())
    provider_registry.register("ollama", OllamaProvider(base_url=settings.ollama_url))
    
    compute_manager = ComputeManager(provider_registry=provider_registry, event_bus=event_bus)
    registry.register("compute_manager", compute_manager)

    # 7. Instantiate & Register Context Layer (ContextManager)
    from switchboard.context.manager import ContextManager
    context_manager = ContextManager(root_path=".", event_bus=event_bus)
    registry.register("context_manager", context_manager)

    # 8. Instantiate Kernel coordinator
    kernel = Kernel(settings=settings, registry=registry)
    logger.info("Kernel bootstrapped and ready for lifecycle initialization")
    
    return kernel
