from uuid import UUID
from switchboard.types.common import BaseEvent

class ProviderLoadedEvent(BaseEvent):
    """Emitted when a compute provider is loaded into the platform."""
    def __init__(self, provider: str) -> None:
        super().__init__(payload={"provider": provider})

    @property
    def provider(self) -> str:
        return self.payload["provider"]


class ProviderUnloadedEvent(BaseEvent):
    """Emitted when the active compute provider is unloaded."""
    def __init__(self, provider: str) -> None:
        super().__init__(payload={"provider": provider})

    @property
    def provider(self) -> str:
        return self.payload["provider"]


class ModelLoadedEvent(BaseEvent):
    """Emitted when a model is successfully loaded by a provider."""
    def __init__(self, model: str, provider: str) -> None:
        super().__init__(payload={"model": model, "provider": provider})

    @property
    def model(self) -> str:
        return self.payload["model"]

    @property
    def provider(self) -> str:
        return self.payload["provider"]


class ModelUnloadedEvent(BaseEvent):
    """Emitted when a model is unloaded from a provider."""
    def __init__(self, model: str, provider: str) -> None:
        super().__init__(payload={"model": model, "provider": provider})

    @property
    def model(self) -> str:
        return self.payload["model"]

    @property
    def provider(self) -> str:
        return self.payload["provider"]


class SessionCreatedEvent(BaseEvent):
    """Emitted when a new compute session is created."""
    def __init__(self, session_id: UUID, model: str) -> None:
        super().__init__(payload={"session_id": str(session_id), "model": model})

    @property
    def session_id(self) -> UUID:
        return UUID(self.payload["session_id"])

    @property
    def model(self) -> str:
        return self.payload["model"]


class SessionTerminatedEvent(BaseEvent):
    """Emitted when a compute session is terminated."""
    def __init__(self, session_id: UUID) -> None:
        super().__init__(payload={"session_id": str(session_id)})

    @property
    def session_id(self) -> UUID:
        return UUID(self.payload["session_id"])


class GenerationStartedEvent(BaseEvent):
    """Emitted when a generation starts inside a compute session."""
    def __init__(self, session_id: UUID, model: str) -> None:
        super().__init__(payload={"session_id": str(session_id), "model": model})

    @property
    def session_id(self) -> UUID:
        return UUID(self.payload["session_id"])

    @property
    def model(self) -> str:
        return self.payload["model"]


class GenerationCompletedEvent(BaseEvent):
    """Emitted when a generation completes successfully."""
    def __init__(self, session_id: UUID, model: str, tokens_used: int) -> None:
        super().__init__(payload={"session_id": str(session_id), "model": model, "tokens_used": tokens_used})

    @property
    def session_id(self) -> UUID:
        return UUID(self.payload["session_id"])

    @property
    def model(self) -> str:
        return self.payload["model"]

    @property
    def tokens_used(self) -> int:
        return self.payload["tokens_used"]


class GenerationFailedEvent(BaseEvent):
    """Emitted when a generation fails inside a compute session."""
    def __init__(self, session_id: UUID, model: str, error: str) -> None:
        super().__init__(payload={"session_id": str(session_id), "model": model, "error": error})

    @property
    def session_id(self) -> UUID:
        return UUID(self.payload["session_id"])

    @property
    def model(self) -> str:
        return self.payload["model"]

    @property
    def error(self) -> str:
        return self.payload["error"]
