from typing import Any, AsyncIterator, Protocol, runtime_checkable
from uuid import UUID
from switchboard.types.runtime import Model, GenerationRequest, GenerationResponse
from switchboard.interfaces.provider import IProvider

@runtime_checkable
class IComputeSession(Protocol):
    """
    Represents an isolated computation context for execution requests,
    tracking call history and cancel-safety.
    """

    @property
    def session_id(self) -> UUID:
        """Unique session identifier."""
        ...

    @property
    def active_model(self) -> str | None:
        """Target model identifier currently used in this session."""
        ...

    async def execute(self, request: GenerationRequest) -> GenerationResponse:
        """
        Execute a complete inference request synchronously within this session.
        """
        ...

    async def execute_stream(self, request: GenerationRequest) -> AsyncIterator[GenerationResponse]:
        """
        Execute a streaming inference request.
        """
        ...

    async def cancel(self) -> None:
        """
        Cancel any ongoing execution in this session.
        """
        ...

    async def get_history(self) -> list[Any]:
        """
        Retrieve history logs (requests and responses) of this session.
        """
        ...


@runtime_checkable
class IComputeLayer(Protocol):
    """
    Core compute layer interface coordinating model registries, providers, and sessions.
    """

    async def load_provider(self, name: str) -> None:
        """
        Activate and load the designated inference provider.
        """
        ...

    async def unload_provider(self) -> None:
        """
        Unload the currently active provider.
        """
        ...

    async def get_active_provider(self) -> IProvider:
        """
        Retrieve the active provider instance.
        """
        ...

    async def list_models(self) -> list[Model]:
        """
        Enumerate all models available from the active provider.
        """
        ...

    async def create_session(self, model_name: str) -> IComputeSession:
        """
        Create a new execution session for the designated model.
        """
        ...

    async def terminate_session(self, session_id: UUID) -> None:
        """
        Safely terminate and release resources of a session.
        """
        ...

    async def health(self) -> bool:
        """
        Check if the compute layer and its loaded backend are operational.
        """
        ...
