from typing import Protocol, Any
from uuid import UUID
from switchboard.interfaces.service import IService
from switchboard.types.task import Task, ResourceRequirements
from switchboard.task.workflow import Workflow

class ISchedulingPolicy(Protocol):
    """Strategy contract to sort ready tasks for scheduler dispatch."""
    
    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """
        Sort candidate tasks to determine dispatch order.
        
        Args:
            tasks: List of ready Tasks to sort.
            
        Returns:
            Sorted list of Task objects.
        """
        ...


class IExecutionEngine(IService, Protocol):
    """Main coordinator orchestrating workflows execution and task scheduling."""
    
    async def submit_workflow(self, workflow: Workflow) -> None:
        """
        Submit a passive Workflow DAG for scheduling and execution.
        
        Args:
            workflow: Passive Workflow graph.
        """
        ...
        
    async def cancel_workflow(self, workflow_name: str) -> None:
        """
        Cancel all active/pending tasks for a named workflow.
        
        Args:
            workflow_name: Target workflow name.
        """
        ...


class IScheduler(Protocol):
    """Manages scheduling loops based on replaceable scheduling policies."""
    
    async def schedule(self) -> None:
        """Scan ready queues and attempt to dispatch eligible tasks."""
        ...


class IResourceAllocator(Protocol):
    """Manages physical hardware locks (RAM, VRAM, GPU allocations)."""
    
    def check_allocation(self, requirements: ResourceRequirements) -> bool:
        """Verify if system requirements can be met currently."""
        ...
        
    def allocate(self, task_id: UUID, requirements: ResourceRequirements) -> None:
        """Lock VRAM/RAM for a task."""
        ...
        
    def release(self, task_id: UUID) -> None:
        """Free VRAM/RAM allocated to a task."""
        ...


class IRetryManager(Protocol):
    """Orchestrates task retry loops and wait backoffs."""
    
    def should_retry(self, task: Task) -> bool:
        """Check if task has retry attempts remaining."""
        ...
        
    def get_backoff_delay(self, task: Task) -> float:
        """Get wait delay in seconds before retry."""
        ...
