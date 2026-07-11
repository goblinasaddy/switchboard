from typing import Protocol, Any
from uuid import UUID
from switchboard.interfaces.service import IService
from switchboard.types.memory import MemoryEntry, MemoryQuery, Reflection

class IMemoryStore(Protocol):
    """Storage-agnostic contract for persisting and loading memory entries."""

    def add_entry(self, entry: MemoryEntry) -> None:
        """
        Persist a memory entry record.
        
        Args:
            entry: MemoryEntry object.
        """
        ...

    def get_entry(self, memory_id: UUID) -> MemoryEntry | None:
        """
        Load a memory entry by its UUID.
        
        Args:
            memory_id: Target memory entry UUID.
            
        Returns:
            MemoryEntry object if found, otherwise None.
        """
        ...

    def query_entries(self, query: MemoryQuery) -> list[MemoryEntry]:
        """
        Query entries using filters and keyword constraints.
        
        Args:
            query: MemoryQuery payload containing search criteria.
            
        Returns:
            List of matching MemoryEntry objects.
        """
        ...

    def update_entry(self, entry: MemoryEntry) -> None:
        """
        Update an existing memory entry.
        
        Args:
            entry: Updated MemoryEntry object.
        """
        ...

    def delete_entry(self, memory_id: UUID) -> None:
        """
        Remove a memory entry.
        
        Args:
            memory_id: UUID of the target memory entry.
        """
        ...


class IMemoryEngine(IService, Protocol):
    """Platform coordinator facilitating memory operations and reflections."""

    async def store_memory(
        self,
        type: str,
        payload: dict[str, Any],
        tags: list[str] | None = None,
        repository_root: str | None = None
    ) -> MemoryEntry:
        """
        Store a new memory entry.
        
        Args:
            type: MemoryType string.
            payload: Key-value contents of the memory.
            tags: Optional list of labels for indexing.
            repository_root: Optional repository root path association.
            
        Returns:
            The created and persisted MemoryEntry.
        """
        ...

    async def retrieve_memories(self, query: MemoryQuery) -> list[MemoryEntry]:
        """
        Query and return ranked memories matching the search criteria.
        
        Args:
            query: MemoryQuery configuration.
            
        Returns:
            List of ranked MemoryEntry matching the query.
        """
        ...

    async def record_reflection(self, reflection: Reflection) -> MemoryEntry:
        """
        Record post-task observations and index them.
        
        Args:
            reflection: Reflection details.
            
        Returns:
            The created and persisted MemoryEntry wrapping the Reflection.
        """
        ...

    async def archive_memory(self, memory_id: UUID) -> None:
        """
        Transition memory lifecycle to ARCHIVED.
        
        Args:
            memory_id: Target memory UUID.
        """
        ...
