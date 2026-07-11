from typing import Any
from uuid import UUID
from switchboard.interfaces.compute import IComputeLayer, IComputeSession
from switchboard.interfaces.service import IService
from switchboard.interfaces.provider import IProvider
from switchboard.interfaces.event_bus import IEventBus
from switchboard.registry.provider import ProviderRegistry
from switchboard.compute.session import ComputeSession
from switchboard.types.runtime import Model
from switchboard.types.events import (
    ProviderLoadedEvent,
    ProviderUnloadedEvent,
    SessionCreatedEvent,
    SessionTerminatedEvent,
)
from switchboard.logging.config import get_logger
from switchboard.exceptions.base import SwitchBoardError

logger = get_logger("compute_manager")

class ComputeManager(IComputeLayer, IService):
    """
    Compute layer manager coordinating registries, provider loading/unloading,
    and compute execution sessions.
    """

    def __init__(self, provider_registry: ProviderRegistry, event_bus: IEventBus | None = None) -> None:
        self._provider_registry = provider_registry
        self._event_bus = event_bus
        self._active_provider: IProvider | None = None
        self._active_provider_name: str | None = None
        self._sessions: dict[UUID, IComputeSession] = {}

    @property
    def name(self) -> str:
        return "compute_manager"

    @property
    def dependencies(self) -> list[str]:
        # Depends on event_bus backbone to propagate events
        return ["event_bus"]

    async def initialize(self) -> None:
        logger.info("Initializing Compute Manager")
        self._sessions.clear()

    async def start(self) -> None:
        logger.info("Compute Manager started")

    async def shutdown(self) -> None:
        logger.info("Shutting down Compute Manager")
        # Terminate all active sessions
        session_ids = list(self._sessions.keys())
        for sid in session_ids:
            try:
                await self.terminate_session(sid)
            except Exception as e:
                logger.error("Error terminating session during shutdown", session_id=str(sid), error=str(e))
                
        # Unload active provider
        if self._active_provider:
            await self.unload_provider()

    # IComputeLayer Interface
    
    async def load_provider(self, name: str) -> None:
        """
        Load a provider backend from the provider registry and initialize it.
        """
        if self._active_provider:
            if self._active_provider_name == name:
                logger.debug("Provider already loaded", provider=name)
                return
            await self.unload_provider()

        logger.info("Loading compute provider", provider=name)
        provider = self._provider_registry.get(name)
        await provider.initialize()
        
        self._active_provider = provider
        self._active_provider_name = name

        if self._event_bus:
            await self._event_bus.publish(ProviderLoadedEvent(name))

    async def unload_provider(self) -> None:
        """
        Unload and shut down the active provider backend.
        """
        if not self._active_provider:
            return

        name = self._active_provider_name or "unknown"
        logger.info("Unloading compute provider", provider=name)
        
        try:
            await self._active_provider.shutdown()
        except Exception as e:
            logger.error("Error during provider shutdown", provider=name, error=str(e))
            
        self._active_provider = None
        self._active_provider_name = None

        if self._event_bus:
            await self._event_bus.publish(ProviderUnloadedEvent(name))

    async def get_active_provider(self) -> IProvider:
        """Get the current active provider instance."""
        if not self._active_provider:
            raise SwitchBoardError("No compute provider is currently loaded.")
        return self._active_provider

    async def list_models(self) -> list[Model]:
        """Enumerate models of the loaded provider."""
        provider = await self.get_active_provider()
        return await provider.list_models()

    async def create_session(self, model_name: str) -> IComputeSession:
        """Create a new compute session utilizing the active provider."""
        provider = await self.get_active_provider()
        
        # Verify model availability
        models = await provider.list_models()
        available_names = [m.name for m in models]
        if model_name not in available_names:
            raise SwitchBoardError(f"Model '{model_name}' is not available on provider '{self._active_provider_name}'.")

        # Instantiate session
        session = ComputeSession(
            model_name=model_name,
            provider=provider,
            event_bus=self._event_bus
        )
        self._sessions[session.session_id] = session

        logger.info("Created compute session", session_id=str(session.session_id), model=model_name)
        if self._event_bus:
            await self._event_bus.publish(SessionCreatedEvent(session.session_id, model_name))

        return session

    async def terminate_session(self, session_id: UUID) -> None:
        """Terminate a compute session and release its resource tracking."""
        if session_id not in self._sessions:
            logger.warning("Attempted to terminate unregistered session", session_id=str(session_id))
            return

        session = self._sessions.pop(session_id)
        await session.cancel()
        
        logger.info("Terminated compute session", session_id=str(session_id))
        if self._event_bus:
            await self._event_bus.publish(SessionTerminatedEvent(session_id))

    async def health(self) -> bool:
        """Check if the active provider is healthy."""
        if not self._active_provider:
            return False
        try:
            return await self._active_provider.health()
        except Exception:
            return False
