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


class TaskCreatedEvent(BaseEvent):
    """Emitted when a new Task is created and registered."""
    def __init__(self, task_id: UUID, name: str) -> None:
        super().__init__(payload={"task_id": str(task_id), "name": name})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])

    @property
    def name(self) -> str:
        return self.payload["name"]


class TaskQueuedEvent(BaseEvent):
    """Emitted when a Task is submitted to the scheduler queue."""
    def __init__(self, task_id: UUID) -> None:
        super().__init__(payload={"task_id": str(task_id)})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])


class TaskStartedEvent(BaseEvent):
    """Emitted when a Task begins running."""
    def __init__(self, task_id: UUID) -> None:
        super().__init__(payload={"task_id": str(task_id)})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])


class TaskPausedEvent(BaseEvent):
    """Emitted when a Task is paused."""
    def __init__(self, task_id: UUID) -> None:
        super().__init__(payload={"task_id": str(task_id)})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])


class TaskCompletedEvent(BaseEvent):
    """Emitted when a Task completes execution successfully."""
    def __init__(self, task_id: UUID, success: bool = True) -> None:
        super().__init__(payload={"task_id": str(task_id), "success": success})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])

    @property
    def success(self) -> bool:
        return self.payload["success"]


class TaskFailedEvent(BaseEvent):
    """Emitted when a Task fails during execution."""
    def __init__(self, task_id: UUID, error: str) -> None:
        super().__init__(payload={"task_id": str(task_id), "error": error})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])

    @property
    def error(self) -> str:
        return self.payload["error"]


class TaskCancelledEvent(BaseEvent):
    """Emitted when a Task is cancelled."""
    def __init__(self, task_id: UUID) -> None:
        super().__init__(payload={"task_id": str(task_id)})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])


class WorkflowStartedEvent(BaseEvent):
    """Emitted when a Workflow run starts."""
    def __init__(self, workflow_name: str) -> None:
        super().__init__(payload={"workflow_name": workflow_name})

    @property
    def workflow_name(self) -> str:
        return self.payload["workflow_name"]


class WorkflowCompletedEvent(BaseEvent):
    """Emitted when a Workflow successfully completes all Tasks."""
    def __init__(self, workflow_name: str) -> None:
        super().__init__(payload={"workflow_name": workflow_name})

    @property
    def workflow_name(self) -> str:
        return self.payload["workflow_name"]


class WorkflowFailedEvent(BaseEvent):
    """Emitted when a Workflow fails (e.g. task retry exhaustion)."""
    def __init__(self, workflow_name: str, error: str) -> None:
        super().__init__(payload={"workflow_name": workflow_name, "error": error})

    @property
    def workflow_name(self) -> str:
        return self.payload["workflow_name"]

    @property
    def error(self) -> str:
        return self.payload["error"]


class TaskScheduledEvent(BaseEvent):
    """Emitted when a Task is enqueued."""
    def __init__(self, task_id: UUID, queue: str) -> None:
        super().__init__(payload={"task_id": str(task_id), "queue": queue})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])

    @property
    def queue(self) -> str:
        return self.payload["queue"]


class TaskDispatchedEvent(BaseEvent):
    """Emitted when a Task is dispatched from scheduler."""
    def __init__(self, task_id: UUID) -> None:
        super().__init__(payload={"task_id": str(task_id)})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])


class ResourcesAllocatedEvent(BaseEvent):
    """Emitted when hardware limits are locked for a Task."""
    def __init__(self, task_id: UUID, vram_gb: float, ram_gb: float) -> None:
        super().__init__(payload={"task_id": str(task_id), "vram_gb": vram_gb, "ram_gb": ram_gb})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])

    @property
    def vram_gb(self) -> float:
        return self.payload["vram_gb"]

    @property
    def ram_gb(self) -> float:
        return self.payload["ram_gb"]


class ResourcesReleasedEvent(BaseEvent):
    """Emitted when locked hardware limits are released."""
    def __init__(self, task_id: UUID) -> None:
        super().__init__(payload={"task_id": str(task_id)})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])


class RetryScheduledEvent(BaseEvent):
    """Emitted when a Task retry is scheduled with delay."""
    def __init__(self, task_id: UUID, retry_count: int, delay_sec: float) -> None:
        super().__init__(payload={"task_id": str(task_id), "retry_count": retry_count, "delay_sec": delay_sec})

    @property
    def task_id(self) -> UUID:
        return UUID(self.payload["task_id"])

    @property
    def retry_count(self) -> int:
        return self.payload["retry_count"]

    @property
    def delay_sec(self) -> float:
        return self.payload["delay_sec"]
