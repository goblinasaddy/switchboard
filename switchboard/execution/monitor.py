from switchboard.execution.queues import QueueManager
from switchboard.execution.allocator import ResourceAllocator
from switchboard.types.execution import ExecutionQueueState, SystemResourceSnapshot

class ExecutionMonitor:
    """
    Exposes real-time system performance telemetry and queue state counts.
    """

    def __init__(self, queue_manager: QueueManager, resource_allocator: ResourceAllocator) -> None:
        self.queue_manager = queue_manager
        self.resource_allocator = resource_allocator

    async def get_queue_state(self) -> ExecutionQueueState:
        """Compile snapshot of queued metrics."""
        return await self.queue_manager.get_queue_state()

    def get_resource_snapshot(self) -> SystemResourceSnapshot:
        """Compile snapshot of locked system allocations."""
        return SystemResourceSnapshot(
            available_vram_gb=self.resource_allocator.max_vram_gb - self.resource_allocator.locked_vram,
            total_vram_gb=self.resource_allocator.max_vram_gb,
            available_ram_gb=self.resource_allocator.max_ram_gb - self.resource_allocator.locked_ram,
            total_ram_gb=self.resource_allocator.max_ram_gb,
            gpu_allocated_count=0
        )
