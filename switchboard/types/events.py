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


class IndexStartedEvent(BaseEvent):
    """Emitted when repository scanner begins scanning codebase files."""
    def __init__(self, root_path: str) -> None:
        super().__init__(payload={"root_path": root_path})

    @property
    def root_path(self) -> str:
        return self.payload["root_path"]


class IndexCompletedEvent(BaseEvent):
    """Emitted when repository scanning and symbol extraction completes successfully."""
    def __init__(self, root_path: str, total_files: int, total_symbols: int) -> None:
        super().__init__(payload={
            "root_path": root_path,
            "total_files": total_files,
            "total_symbols": total_symbols
        })

    @property
    def root_path(self) -> str:
        return self.payload["root_path"]

    @property
    def total_files(self) -> int:
        return self.payload["total_files"]

    @property
    def total_symbols(self) -> int:
        return self.payload["total_symbols"]


class IndexFailedEvent(BaseEvent):
    """Emitted when repository scanning fails."""
    def __init__(self, root_path: str, error: str) -> None:
        super().__init__(payload={"root_path": root_path, "error": error})

    @property
    def root_path(self) -> str:
        return self.payload["root_path"]

    @property
    def error(self) -> str:
        return self.payload["error"]


class FileParsedEvent(BaseEvent):
    """Emitted when a single file is successfully parsed into AST symbols."""
    def __init__(self, file_path: str, symbols_count: int) -> None:
        super().__init__(payload={"file_path": file_path, "symbols_count": symbols_count})

    @property
    def file_path(self) -> str:
        return self.payload["file_path"]

    @property
    def symbols_count(self) -> int:
        return self.payload["symbols_count"]


class ContextBuiltEvent(BaseEvent):
    """Emitted when a query-specific ContextPackage is successfully compiled."""
    def __init__(self, query: str, files_count: int, symbols_count: int) -> None:
        super().__init__(payload={
            "query": query,
            "files_count": files_count,
            "symbols_count": symbols_count
        })

    @property
    def query(self) -> str:
        return self.payload["query"]

    @property
    def files_count(self) -> int:
        return self.payload["files_count"]

    @property
    def symbols_count(self) -> int:
        return self.payload["symbols_count"]
