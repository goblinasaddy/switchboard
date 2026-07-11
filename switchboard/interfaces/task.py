from typing import Protocol
from uuid import UUID
from switchboard.interfaces.service import IService
from switchboard.types.task import Task, TaskContext, TaskPriority

class ITaskManager(IService, Protocol):
    """Protocol for task orchestration and lifecycle management."""

    async def create_task(
        self,
        name: str,
        objective: str,
        context: TaskContext,
        priority: TaskPriority = TaskPriority.DEFAULT
    ) -> Task:
        """
        Create a new task and associate it with the registered context.
        
        Args:
            name: Human-readable name of the task.
            objective: High-level description of what needs to be solved.
            context: Context details associated with the execution.
            priority: Priority weighting of the task.
            
        Returns:
            The created Task object.
        """
        ...

    async def submit_task(self, task_id: UUID) -> None:
        """
        Submit a task to the queue for execution.
        
        Args:
            task_id: UUID of the task to submit.
        """
        ...

    async def get_task(self, task_id: UUID) -> Task:
        """
        Retrieve a task by its UUID.
        
        Args:
            task_id: Target task ID.
            
        Returns:
            Task object.
        """
        ...

    async def cancel_task(self, task_id: UUID) -> None:
        """
        Cancel a running or queued task.
        
        Args:
            task_id: UUID of the task to cancel.
        """
        ...
