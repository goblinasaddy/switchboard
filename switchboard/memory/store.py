import os
import json
from uuid import UUID
from switchboard.interfaces.memory import IMemoryStore
from switchboard.types.memory import MemoryEntry, MemoryQuery, MemoryType

class InMemoryStore(IMemoryStore):
    """
    Volatile in-memory dictionary-backed store implementation of IMemoryStore.
    """

    def __init__(self) -> None:
        self._entries: dict[UUID, MemoryEntry] = {}

    def add_entry(self, entry: MemoryEntry) -> None:
        self._entries[entry.memory_id] = entry

    def get_entry(self, memory_id: UUID) -> MemoryEntry | None:
        return self._entries.get(memory_id)

    def query_entries(self, query: MemoryQuery) -> list[MemoryEntry]:
        results = []
        for entry in self._entries.values():
            # Filter by repository root if queried
            if query.repository_root and entry.repository_root != query.repository_root:
                continue
            # Filter by type lists if queried
            if query.types and entry.type not in query.types:
                continue
            # Filter by tags if queried (all queried tags must match)
            if query.tags and not all(t in entry.tags for t in query.tags):
                continue
            results.append(entry)
        return results

    def update_entry(self, entry: MemoryEntry) -> None:
        if entry.memory_id in self._entries:
            self._entries[entry.memory_id] = entry

    def delete_entry(self, memory_id: UUID) -> None:
        self._entries.pop(memory_id, None)


class JSONFileStore(IMemoryStore):
    """
    Persistent filesystem JSON file store implementation of IMemoryStore.
    """

    def __init__(self, file_path: str = ".switchboard/memory.json") -> None:
        self.file_path = os.path.abspath(file_path)
        self._entries: dict[UUID, MemoryEntry] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry_data in data:
                    entry = MemoryEntry.model_validate(entry_data)
                    self._entries[entry.memory_id] = entry
        except Exception:
            # Fallback for parsing errors or corrupted files
            self._entries = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                data = [entry.model_dump(mode="json") for entry in self._entries.values()]
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def add_entry(self, entry: MemoryEntry) -> None:
        self._entries[entry.memory_id] = entry
        self._save()

    def get_entry(self, memory_id: UUID) -> MemoryEntry | None:
        return self._entries.get(memory_id)

    def query_entries(self, query: MemoryQuery) -> list[MemoryEntry]:
        results = []
        for entry in self._entries.values():
            if query.repository_root and entry.repository_root != query.repository_root:
                continue
            if query.types and entry.type not in query.types:
                continue
            if query.tags and not all(t in entry.tags for t in query.tags):
                continue
            results.append(entry)
        return results

    def update_entry(self, entry: MemoryEntry) -> None:
        if entry.memory_id in self._entries:
            self._entries[entry.memory_id] = entry
            self._save()

    def delete_entry(self, memory_id: UUID) -> None:
        if self._entries.pop(memory_id, None):
            self._save()
