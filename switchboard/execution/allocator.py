from uuid import UUID
from switchboard.interfaces.execution import IResourceAllocator
from switchboard.types.task import ResourceRequirements

class ResourceAllocator(IResourceAllocator):
    """
    Tracks and locks hardware constraints (VRAM/RAM) to prevent overallocation.
    """

    def __init__(self, max_vram_gb: float = 12.0, max_ram_gb: float = 16.0) -> None:
        self.max_vram_gb = max_vram_gb
        self.max_ram_gb = max_ram_gb
        self._locked_vram = 0.0
        self._locked_ram = 0.0
        self._allocations: dict[UUID, ResourceRequirements] = {}

    @property
    def locked_vram(self) -> float:
        return self._locked_vram

    @property
    def locked_ram(self) -> float:
        return self._locked_ram

    def check_allocation(self, requirements: ResourceRequirements) -> bool:
        """Verify if target resources are currently allocatable."""
        if self._locked_vram + requirements.estimated_vram_gb > self.max_vram_gb:
            return False
        if self._locked_ram + requirements.estimated_ram_gb > self.max_ram_gb:
            return False
        return True

    def allocate(self, task_id: UUID, requirements: ResourceRequirements) -> None:
        """Lock VRAM and RAM for a task."""
        if not self.check_allocation(requirements):
            raise ValueError(f"Insufficient resources to allocate task '{task_id}'.")
            
        self._locked_vram += requirements.estimated_vram_gb
        self._locked_ram += requirements.estimated_ram_gb
        self._allocations[task_id] = requirements

    def release(self, task_id: UUID) -> None:
        """Free VRAM and RAM allocated to a task."""
        requirements = self._allocations.pop(task_id, None)
        if requirements:
            self._locked_vram = max(0.0, self._locked_vram - requirements.estimated_vram_gb)
            self._locked_ram = max(0.0, self._locked_ram - requirements.estimated_ram_gb)
