import time
from switchboard.types.memory import MemoryEntry, MemoryType, MemoryLifecycle, Reflection

class ReflectionHelper:
    """
    Utility compiler wrapping Reflection objects into canonical MemoryEntry indexes.
    """

    @staticmethod
    def compile_entry(reflection: Reflection) -> MemoryEntry:
        """Converts Reflection into a MemoryEntry ready for storage."""
        # Setup tags containing task links
        tags = ["reflection", f"task_{reflection.task_id}"]
        # Inherit metrics and recommendations into query tags if present
        for rec in reflection.recommendations:
            # Add shortened word tags if simple
            words = rec.lower().split()[:2]
            tags.extend(w for w in words if len(w) > 2)
            
        now = time.time()
        # Set timestamp if not set
        if reflection.created_at == 0.0:
            reflection.created_at = now

        return MemoryEntry(
            type=MemoryType.REFLECTION,
            lifecycle=MemoryLifecycle.INDEXED,
            task_id=reflection.task_id,
            tags=list(set(tags)),
            payload=reflection.model_dump(mode="json"),
            created_at=now,
            updated_at=now
        )
