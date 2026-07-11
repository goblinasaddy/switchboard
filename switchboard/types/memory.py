from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Any

class MemoryType(str, Enum):
    EXECUTION = "execution"
    CONTEXT = "context"
    REFLECTION = "reflection"
    KNOWLEDGE = "knowledge"

class MemoryLifecycle(str, Enum):
    CREATED = "created"
    INDEXED = "indexed"
    RETRIEVED = "retrieved"
    UPDATED = "updated"
    ARCHIVED = "archived"
    EXPIRED = "expired"

class MemoryEntry(BaseModel):
    memory_id: UUID = Field(default_factory=uuid4)
    type: MemoryType
    lifecycle: MemoryLifecycle = MemoryLifecycle.CREATED
    repository_root: str | None = None
    task_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0
    access_count: int = 0
    last_accessed_at: float | None = None

class Reflection(BaseModel):
    reflection_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    what_worked: str
    what_failed: str
    recommendations: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0

class MemoryQuery(BaseModel):
    query_text: str | None = None
    types: list[MemoryType] | None = None
    tags: list[str] | None = None
    repository_root: str | None = None
    limit: int = 10
