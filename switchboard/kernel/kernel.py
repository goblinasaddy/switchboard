from typing import Any
from switchboard.config.settings import Settings
from switchboard.interfaces.service import IService
from switchboard.registry.service import ServiceRegistry
from switchboard.kernel.state import KernelState
from switchboard.kernel.lifecycle import LifecycleEvent, ServiceLifecycleEvent
from switchboard.logging.config import get_logger
from switchboard.exceptions.base import KernelError

logger = get_logger("kernel")

class Kernel:
    """
    The orchestrator and central control unit of the SwitchBoard platform.
    Coordinates initialization, startup, and shutdown sequences for all registered subsystems.
    """

    def __init__(self, settings: Settings, registry: ServiceRegistry) -> None:
        self._settings = settings
        self._registry = registry
        self._state = KernelState.UNINITIALIZED

    @property
    def state(self) -> KernelState:
        """Current lifecycle state of the kernel."""
        return self._state

    @property
    def settings(self) -> Settings:
        """System configuration settings loaded during bootstrap."""
        return self._settings

    @property
    def registry(self) -> ServiceRegistry:
        """Service registry holding all managed subsystems."""
        return self._registry

    def get_service(self, name: str) -> Any:
        """Helper method to access a registered service by name."""
        return self._registry.get(name)

    async def _transition_state(self, to_state: KernelState, details: str = "") -> None:
        from_state = self._state
        self._state = to_state
        logger.info(
            "Kernel state transition", 
            from_state=from_state.value, 
            to_state=to_state.value, 
            details=details
        )
        
        # Publish lifecycle event if the event_bus service is registered and started
        if self._registry.has("event_bus"):
            try:
                event_bus = self.get_service("event_bus")
                # Avoid publishing on event_bus before it starts or after it stops
                await event_bus.publish(LifecycleEvent(from_state, to_state, details))
            except Exception as e:
                logger.error("Failed to publish LifecycleEvent", error=str(e))

    async def initialize(self) -> None:
        """
        Initialize all registered services in topological dependency order.
        """
        if self._state != KernelState.UNINITIALIZED:
            raise KernelError(f"Cannot initialize Kernel when in state: {self._state.value}")

        await self._transition_state(KernelState.INITIALIZING, "Initializing all subsystems")

        try:
            ordered_services = self._registry.get_ordered_services()
            for service in ordered_services:
                logger.info("Initializing service", service=service.name)
                try:
                    await service.initialize()
                    await self._publish_service_event(service.name, "initialize", success=True)
                except Exception as e:
                    await self._publish_service_event(service.name, "initialize", success=False, error_msg=str(e))
                    raise KernelError(f"Service '{service.name}' failed to initialize: {e}") from e

        except Exception as e:
            await self._transition_state(KernelState.ERROR, f"Initialization failed: {e}")
            raise

    async def start(self) -> None:
        """
        Start all registered services in topological dependency order.
        """
        if self._state != KernelState.INITIALIZING:
            raise KernelError(f"Kernel must be INITIALIZING to start. Current state: {self._state.value}")

        try:
            ordered_services = self._registry.get_ordered_services()
            for service in ordered_services:
                logger.info("Starting service", service=service.name)
                try:
                    await service.start()
                    await self._publish_service_event(service.name, "start", success=True)
                except Exception as e:
                    await self._publish_service_event(service.name, "start", success=False, error_msg=str(e))
                    raise KernelError(f"Service '{service.name}' failed to start: {e}") from e

            await self._transition_state(KernelState.RUNNING, "All subsystems started successfully")
        except Exception as e:
            await self._transition_state(KernelState.ERROR, f"Startup failed: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Shutdown all registered services in reverse topological dependency order.
        """
        if self._state not in (KernelState.RUNNING, KernelState.ERROR, KernelState.INITIALIZING):
            logger.warning("Shutdown invoked on non-active Kernel state", state=self._state.value)
            return

        await self._transition_state(KernelState.SHUTTING_DOWN, "Shutting down all subsystems")

        try:
            # Shutdown in reverse topological order (dependents shut down BEFORE dependencies)
            ordered_services = list(reversed(self._registry.get_ordered_services()))
            for service in ordered_services:
                if service.name == "event_bus":
                    continue
                logger.info("Shutting down service", service=service.name)
                try:
                    await service.shutdown()
                    await self._publish_service_event(service.name, "shutdown", success=True)
                except Exception as e:
                    logger.error("Error during service shutdown", service=service.name, error=str(e))
                    await self._publish_service_event(service.name, "shutdown", success=False, error_msg=str(e))

            # Transition to STOPPED state before shutting down the communication backbone (Event Bus)
            await self._transition_state(KernelState.STOPPED, "All subsystems stopped successfully")

            # Finally shut down the Event Bus itself
            if self._registry.has("event_bus"):
                try:
                    await self.get_service("event_bus").shutdown()
                except Exception as e:
                    logger.error("Error during Event Bus shutdown", error=str(e))

        except Exception as e:
            await self._transition_state(KernelState.ERROR, f"Shutdown encountered errors: {e}")
            raise

    async def _publish_service_event(
        self, 
        service_name: str, 
        action: str, 
        success: bool, 
        error_msg: str | None = None
    ) -> None:
        if self._registry.has("event_bus") and service_name != "event_bus":
            try:
                event_bus = self.get_service("event_bus")
                await event_bus.publish(ServiceLifecycleEvent(service_name, action, success, error_msg))
            except Exception as e:
                logger.error("Failed to publish ServiceLifecycleEvent", error=str(e))
