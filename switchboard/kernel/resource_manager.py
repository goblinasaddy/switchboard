from switchboard.interfaces.service import IService
from switchboard.logging.config import get_logger
from switchboard.exceptions.base import KernelError

logger = get_logger("resource_manager")

class ResourceManager(IService):
    """
    Subsystem responsible for monitoring and allocating physical system resources
    (VRAM, RAM, CPU threads) for local AI execution.
    """

    def __init__(self, max_vram_gb: float = 12.0, max_ram_gb: float = 16.0) -> None:
        self._max_vram_gb = max_vram_gb
        self._max_ram_gb = max_ram_gb
        
        # Allocations tracking
        self._allocated_vram_gb = 0.0
        self._allocated_ram_gb = 0.0
        self._active_allocations: dict[str, dict[str, float]] = {}

    @property
    def name(self) -> str:
        return "resource_manager"

    @property
    def dependencies(self) -> list[str]:
        # The resource manager initializes independently
        return []

    async def initialize(self) -> None:
        logger.info(
            "Initializing Resource Manager", 
            max_vram_gb=self._max_vram_gb, 
            max_ram_gb=self._max_ram_gb
        )
        self._allocated_vram_gb = 0.0
        self._allocated_ram_gb = 0.0
        self._active_allocations.clear()

    async def start(self) -> None:
        logger.info("Resource Manager started and actively monitoring allocations")

    async def shutdown(self) -> None:
        logger.info("Releasing all tracked resource allocations")
        self._allocated_vram_gb = 0.0
        self._allocated_ram_gb = 0.0
        self._active_allocations.clear()

    # Public Resource Allocation APIs (Stub implementation for Phase 0)
    
    def get_available_vram(self) -> float:
        """Get remaining unallocated VRAM in Gigabytes."""
        return max(0.0, self._max_vram_gb - self._allocated_vram_gb)

    def get_available_ram(self) -> float:
        """Get remaining unallocated RAM in Gigabytes."""
        return max(0.0, self._max_ram_gb - self._allocated_ram_gb)

    def allocate(self, consumer_id: str, vram_gb: float, ram_gb: float) -> None:
        """
        Request allocation of VRAM and RAM.
        
        Args:
            consumer_id: String key identifying the component requesting resources (e.g. model run name).
            vram_gb: Requested VRAM in Gigabytes.
            ram_gb: Requested RAM in Gigabytes.
            
        Raises:
            KernelError: If allocating exceeds configured limits.
        """
        if consumer_id in self._active_allocations:
            raise KernelError(f"Resource consumer '{consumer_id}' already has active allocations.")

        if self._allocated_vram_gb + vram_gb > self._max_vram_gb:
            raise KernelError(
                f"Cannot allocate {vram_gb} GB VRAM. Exceeds remaining capacity of "
                f"{self.get_available_vram()} GB (Max: {self._max_vram_gb} GB)."
            )

        if self._allocated_ram_gb + ram_gb > self._max_ram_gb:
            raise KernelError(
                f"Cannot allocate {ram_gb} GB RAM. Exceeds remaining capacity of "
                f"{self.get_available_ram()} GB (Max: {self._max_ram_gb} GB)."
            )

        self._allocated_vram_gb += vram_gb
        self._allocated_ram_gb += ram_gb
        self._active_allocations[consumer_id] = {"vram_gb": vram_gb, "ram_gb": ram_gb}
        
        logger.debug(
            "Allocated resources", 
            consumer=consumer_id, 
            vram_gb=vram_gb, 
            ram_gb=ram_gb,
            total_allocated_vram=self._allocated_vram_gb,
            total_allocated_ram=self._allocated_ram_gb
        )

    def release(self, consumer_id: str) -> None:
        """
        Release resource allocation for the consumer.
        
        Args:
            consumer_id: String key identifying the consumer.
        """
        if consumer_id not in self._active_allocations:
            logger.warning("Attempted to release resources for unregistered consumer", consumer=consumer_id)
            return

        allocs = self._active_allocations.pop(consumer_id)
        self._allocated_vram_gb -= allocs["vram_gb"]
        self._allocated_ram_gb -= allocs["ram_gb"]

        logger.debug(
            "Released resources", 
            consumer=consumer_id, 
            vram_gb=allocs["vram_gb"], 
            ram_gb=allocs["ram_gb"],
            total_allocated_vram=self._allocated_vram_gb,
            total_allocated_ram=self._allocated_ram_gb
        )
