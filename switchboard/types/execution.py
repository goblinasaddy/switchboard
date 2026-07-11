from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Any

class ExecutionQueueStatus(str, Enum):
    WAITING = "waiting"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"

class SystemResourceSnapshot(BaseModel):
    available_vram_gb: float
    total_vram_gb: float
    available_ram_gb: float
    total_ram_gb: float
    gpu_allocated_count: int

class ExecutionQueueState(BaseModel):
    waiting_count: int = 0
    ready_count: int = 0
    running_count: int = 0
    blocked_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    active_vram_allocated_gb: float = 0.0

class WorkflowState(BaseModel):
    workflow_id: UUID = Field(default_factory=uuid4)
    name: str
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0
    status: str = "created"  # running, completed, failed
