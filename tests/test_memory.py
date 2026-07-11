import pytest
import os
import tempfile
import time
from uuid import uuid4
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.types.memory import MemoryEntry, MemoryQuery, MemoryType, MemoryLifecycle, Reflection
from switchboard.memory.store import InMemoryStore, JSONFileStore
from switchboard.memory.retrieval import MemoryRanker
from switchboard.types.events import (
    MemoryCreatedEvent,
    MemoryRetrievedEvent,
    ReflectionStoredEvent,
)

def test_in_memory_store_crud() -> None:
    store = InMemoryStore()
    
    # Create entry
    entry = MemoryEntry(
        type=MemoryType.KNOWLEDGE,
        repository_root="/tmp/repo",
        tags=["pattern", "di"],
        payload={"convention": "use constructor injection"}
    )
    
    # Add
    store.add_entry(entry)
    assert store.get_entry(entry.memory_id) is not None
    
    # Query match
    query = MemoryQuery(types=[MemoryType.KNOWLEDGE], tags=["di"], repository_root="/tmp/repo")
    results = store.query_entries(query)
    assert len(results) == 1
    assert results[0].payload["convention"] == "use constructor injection"
    
    # Query mismatch repository
    query_wrong_repo = MemoryQuery(types=[MemoryType.KNOWLEDGE], tags=["di"], repository_root="/other/repo")
    assert len(store.query_entries(query_wrong_repo)) == 0
    
    # Update
    entry.payload["convention"] = "updated di"
    store.update_entry(entry)
    assert store.get_entry(entry.memory_id).payload["convention"] == "updated di"
    
    # Delete
    store.delete_entry(entry.memory_id)
    assert store.get_entry(entry.memory_id) is None


def test_json_file_store_persistence() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "mem.json")
        store = JSONFileStore(file_path=file_path)
        
        entry = MemoryEntry(
            type=MemoryType.EXECUTION,
            tags=["run_metrics"],
            payload={"latency_ms": 450}
        )
        
        store.add_entry(entry)
        assert os.path.exists(file_path)
        
        # Instantiate second store pointing to same file
        second_store = JSONFileStore(file_path=file_path)
        loaded = second_store.get_entry(entry.memory_id)
        assert loaded is not None
        assert loaded.payload["latency_ms"] == 450


def test_retrieval_relevance_ranking() -> None:
    ranker = MemoryRanker()
    now = time.time()
    
    # Entry A: 2 tags matching query tags ['ast', 'py']
    entry_a = MemoryEntry(
        type=MemoryType.CONTEXT,
        tags=["ast", "py"],
        payload={"file": "a.py"},
        created_at=now - 1000
    )
    # Entry B: 3 tags matching query tags ['ast', 'py', 'parser']
    entry_b = MemoryEntry(
        type=MemoryType.CONTEXT,
        tags=["ast", "py", "parser"],
        payload={"file": "b.py"},
        created_at=now - 500
    )
    # Entry C: No tags matching
    entry_c = MemoryEntry(
        type=MemoryType.CONTEXT,
        tags=["rust"],
        payload={"file": "c.rs"},
        created_at=now
    )
    
    query = MemoryQuery(tags=["ast", "py"])
    entries = [entry_a, entry_b, entry_c]
    
    ranked = ranker.rank(entries, query)
    
    # Entry C should be filtered out by search tag filters if query ran through store,
    # but ranker scores all candidates. Let's assert rankings:
    # Entry B has 2 matching tags: 'ast', 'py'. Entry A has 2 matching tags: 'ast', 'py'.
    # Entry B is newer (created_at is closer to now), so it should rank higher than A due to recency boost!
    assert ranked[0].payload["file"] == "b.py"
    assert ranked[1].payload["file"] == "a.py"


@pytest.mark.asyncio
async def test_memory_engine_events_and_reflections() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    event_bus = kernel.get_service("event_bus")
    memory_engine = kernel.get_service("memory_engine")
    
    # Track events
    events = []
    async def log_event(event) -> None:
        events.append(event)
        
    await event_bus.subscribe(MemoryCreatedEvent, log_event)
    await event_bus.subscribe(MemoryRetrievedEvent, log_event)
    await event_bus.subscribe(ReflectionStoredEvent, log_event)
    
    # Test Store
    entry = await memory_engine.store_memory(
        type="knowledge",
        payload={"pattern": "pipeline"},
        tags=["design"]
    )
    assert entry.lifecycle == MemoryLifecycle.INDEXED
    
    # Test Retrieve
    query = MemoryQuery(types=[MemoryType.KNOWLEDGE], tags=["design"])
    retrieved = await memory_engine.retrieve_memories(query)
    assert len(retrieved) == 1
    assert retrieved[0].access_count == 1
    assert retrieved[0].lifecycle == MemoryLifecycle.RETRIEVED
    
    # Test Record Reflection
    ref = Reflection(
        task_id=uuid4(),
        what_worked="mock tests",
        what_failed="none",
        recommendations=["continue testing"]
    )
    ref_entry = await memory_engine.record_reflection(ref)
    assert ref_entry.type == MemoryType.REFLECTION
    assert "reflection" in ref_entry.tags
    
    # Check event triggers
    event_types = [type(e) for e in events]
    assert MemoryCreatedEvent in event_types
    assert MemoryRetrievedEvent in event_types
    assert ReflectionStoredEvent in event_types
    
    await kernel.shutdown()
