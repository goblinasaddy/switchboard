from typing import Protocol, runtime_checkable

@runtime_checkable
class IService(Protocol):
    """
    Interface defining the lifecycle contract for all SwitchBoard services.
    
    Subsystems that function as long-running platform modules must implement this
    protocol to be managed by the Service Registry and Kernel.
    """

    @property
    def name(self) -> str:
        """Unique identifier name of the service."""
        ...

    @property
    def dependencies(self) -> list[str]:
        """Names of other services this service depends on."""
        ...

    async def initialize(self) -> None:
        """
        Perform internal setup, setup directories, validate config.
        Called once before startup.
        """
        ...

    async def start(self) -> None:
        """
        Activate background tasks, bind to event queues, start loops.
        Called once to start runtime execution.
        """
        ...

    async def shutdown(self) -> None:
        """
        Clean up resources, flush logs, cancel tasks, shut down child processes.
        Called once to safely stop the service.
        """
        ...
