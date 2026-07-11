from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Any

class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(int, Enum):
    LOW = 0
    DEFAULT = 1
    HIGH = 2
    CRITICAL = 3

class ArtifactType(str, Enum):
    PATCH = "patch"
    MARKDOWN = "markdown"
    CODE = "code"
    REPORT = "report"
    LOG = "log"
    IMAGE = "image"
    METRICS = "metrics"
    UNKNOWN = "unknown"

class Artifact(BaseModel):
    artifact_id: UUID = Field(default_factory=uuid4)
    name: str
    type: ArtifactType = ArtifactType.UNKNOWN
    path: str | None = None
    content: Any = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResourceRequirements(BaseModel):
    estimated_vram_gb: float = 0.0
    estimated_ram_gb: float = 0.0
    requires_gpu: bool = False
    max_execution_time_sec: int = 3600

class TaskContext(BaseModel):
    context_id: UUID = Field(default_factory=uuid4)
    repository_root: str | None = None
    target_files: list[str] = Field(default_factory=list)
    issue_description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExecutionPlan(BaseModel):
    steps: list[str] = Field(default_factory=list)
    strategy: str = "sequential"
    requirements: ResourceRequirements = Field(default_factory=ResourceRequirements)

class TaskResult(BaseModel):
    status: TaskStatus
    output: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    tokens_consumed: int = 0
    artifacts: list[Artifact] = Field(default_factory=list)

class Task(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    name: str
    objective: str
    status: TaskStatus = TaskStatus.CREATED
    priority: TaskPriority = TaskPriority.DEFAULT
    context_id: UUID
    requirements: ResourceRequirements = Field(default_factory=ResourceRequirements)
    dependencies: list[UUID] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    result: TaskResult | None = None
    created_at: float = Field(default_factory=lambda: 0.0)
    started_at: float | None = None
    finished_at: float | None = None
