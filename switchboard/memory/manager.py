import time
from uuid import UUID
from typing import Any
from switchboard.interfaces.memory import IMemoryEngine, IMemoryStore
from switchboard.interfaces.service import IService
from switchboard.interfaces.event_bus import IEventBus
from switchboard.types.memory import MemoryEntry, MemoryQuery, MemoryType, MemoryLifecycle, Reflection
from switchboard.types.events import (
    MemoryCreatedEvent,
    MemoryUpdatedEvent,
    MemoryRetrievedEvent,
    MemoryArchivedEvent,
    ReflectionStoredEvent,
)
from switchboard.memory.store import InMemoryStore
from switchboard.memory.retrieval import MemoryRanker
from switchboard.memory.reflection import ReflectionHelper
from switchboard.logging.config import get_logger

logger = get_logger("memory_engine")

class MemoryEngine(IMemoryEngine, IService):
    """
    Subsystem coordinator managing store connections, queries ranking,
    retrievals, post-task reflections, and event broadcasts.
    """

    def __init__(self, store: IMemoryStore | None = None, event_bus: IEventBus | None = None) -> None:
        self._store = store or InMemoryStore()
        self._event_bus = event_bus
        self._ranker = MemoryRanker()

    @property
    def store(self) -> IMemoryStore:
        return self._store

    @property
    def name(self) -> str:
        return "memory_engine"

    @property
    def dependencies(self) -> list[str]:
        return ["event_bus"]

    async def initialize(self) -> None:
        logger.info("Initializing Memory Engine", store_type=self._store.__class__.__name__)

    async def start(self) -> None:
        logger.info("Memory Engine started")

    async def shutdown(self) -> None:
        logger.info("Shutting down Memory Engine")

    # IMemoryEngine Interface

    async def store_memory(
        self,
        type: str,
        payload: dict[str, Any],
        tags: list[str] | None = None,
        repository_root: str | None = None
    ) -> MemoryEntry:
        """Store a new MemoryEntry record."""
        now = time.time()
        entry = MemoryEntry(
            type=MemoryType(type),
            lifecycle=MemoryLifecycle.INDEXED,
            repository_root=repository_root,
            tags=tags or [],
            payload=payload,
            created_at=now,
            updated_at=now
        )
        
        self._store.add_entry(entry)
        logger.info("Recorded MemoryEntry", memory_id=str(entry.memory_id), type=entry.type.value)
        
        if self._event_bus:
            await self._event_bus.publish(MemoryCreatedEvent(entry.memory_id, entry.type.value))
            
        return entry

    async def retrieve_memories(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Query and return sorted relevant entries."""
        # 1. Fetch matching entries from store
        candidates = self._store.query_entries(query)
        
        # 2. Sort candidates using MemoryRanker
        ranked = self._ranker.rank(candidates, query)
        
        # 3. Update entry access metrics (popularity)
        now = time.time()
        for entry in ranked:
            entry.access_count += 1
            entry.last_accessed_at = now
            entry.lifecycle = MemoryLifecycle.RETRIEVED
            self._store.update_entry(entry)
            
        logger.info("Retrieved relevant memories", query=query.query_text, matched_count=len(ranked))
        
        if self._event_bus:
            await self._event_bus.publish(MemoryRetrievedEvent(query.query_text, len(ranked)))
            
        return ranked

    async def record_reflection(self, reflection: Reflection) -> MemoryEntry:
        """Compile post-task outcomes and index them into Reflection memory."""
        # 1. Convert Reflection to MemoryEntry
        entry = ReflectionHelper.compile_entry(reflection)
        
        # 2. Persist
        self._store.add_entry(entry)
        logger.info("Recorded post-task Reflection", reflection_id=str(reflection.reflection_id), task_id=str(reflection.task_id))
        
        # 3. Broadcast events
        if self._event_bus:
            await self._event_bus.publish(ReflectionStoredEvent(reflection.reflection_id, reflection.task_id))
            await self._event_bus.publish(MemoryCreatedEvent(entry.memory_id, entry.type.value))
            
        return entry

    async def archive_memory(self, memory_id: UUID) -> None:
        """Archive target memory by transitioning its lifecycle."""
        entry = self._store.get_entry(memory_id)
        if not entry:
            logger.warning("Attempted to archive non-existent memory entry", memory_id=str(memory_id))
            return
            
        entry.lifecycle = MemoryLifecycle.ARCHIVED
        entry.updated_at = time.time()
        
        self._store.update_entry(entry)
        logger.info("Archived MemoryEntry", memory_id=str(memory_id))
        
        if self._event_bus:
            await self._event_bus.publish(MemoryArchivedEvent(memory_id))
