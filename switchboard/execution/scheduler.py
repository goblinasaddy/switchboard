import asyncio
from typing import Callable, Coroutine
from uuid import UUID
from switchboard.interfaces.execution import IScheduler, ISchedulingPolicy, IResourceAllocator
from switchboard.interfaces.event_bus import IEventBus
from switchboard.types.task import Task, TaskStatus
from switchboard.types.execution import ExecutionQueueStatus
from switchboard.types.events import (
    TaskDispatchedEvent,
    ResourcesAllocatedEvent,
)
from switchboard.execution.queues import QueueManager
from switchboard.logging.config import get_logger

logger = get_logger("scheduler")

class PriorityVRAMPolicy(ISchedulingPolicy):
    """Sorts tasks by Priority (Critical first) and then FIFO (creation_time)."""
    
    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        # Priority is an enum with LOW=0, DEFAULT=1, HIGH=2, CRITICAL=3
        # Sort in descending order of priority, and ascending order of created_at
        return sorted(tasks, key=lambda t: (-t.priority.value, t.created_at))


class FIFOPolicy(ISchedulingPolicy):
    """Sorts tasks strictly by creation time (FIFO)."""
    
    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda t: t.created_at)


class SequentialPolicy(ISchedulingPolicy):
    """Sorts strictly by creation time, representing a single-execution queue."""
    
    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda t: t.created_at)


class Scheduler(IScheduler):
    """
    Core Scheduler walking through eligible task queues and dispatching
    tasks using a pluggable SchedulingPolicy strategy.
    """

    def __init__(
        self,
        queue_manager: QueueManager,
        resource_allocator: IResourceAllocator,
        policy: ISchedulingPolicy,
        dispatch_fn: Callable[[Task], Coroutine[None, None, None]],
        event_bus: IEventBus | None = None
    ) -> None:
        self.queue_manager = queue_manager
        self.resource_allocator = resource_allocator
        self.policy = policy
        self.dispatch_fn = dispatch_fn
        self.event_bus = event_bus

    async def schedule(self) -> None:
        """Scan ready/blocked queues and dispatch tasks under hardware constraints."""
        # Retrieve all tasks in READY and BLOCKED states
        ready_tasks = await self.queue_manager.get_tasks_in_queue(ExecutionQueueStatus.READY)
        blocked_tasks = await self.queue_manager.get_tasks_in_queue(ExecutionQueueStatus.BLOCKED)
        
        candidates = ready_tasks + blocked_tasks
        if not candidates:
            return

        # Pluggable scheduling policy strategy sorting
        sorted_candidates = self.policy.sort_tasks(candidates)
        
        # If using SequentialPolicy, check if any task is already RUNNING. If yes, block everything else.
        if isinstance(self.policy, SequentialPolicy):
            running = await self.queue_manager.get_tasks_in_queue(ExecutionQueueStatus.RUNNING)
            if running:
                logger.debug("Sequential policy active and task is currently running. Dispatch paused.")
                return

        for task in sorted_candidates:
            req = task.requirements
            
            # Check allocation
            if self.resource_allocator.check_allocation(req):
                # Lock resources
                self.resource_allocator.allocate(task.task_id, req)
                
                # Update queue state to RUNNING
                await self.queue_manager.move_task(task.task_id, ExecutionQueueStatus.RUNNING)
                
                logger.info("Scheduler dispatched task", task_id=str(task.task_id), priority=task.priority.value)
                
                # Fire events
                if self.event_bus:
                    await self.event_bus.publish(ResourcesAllocatedEvent(task.task_id, req.estimated_vram_gb, req.estimated_ram_gb))
                    await self.event_bus.publish(TaskDispatchedEvent(task.task_id))
                    
                # Dispatch execution asynchronously
                asyncio.create_task(self.dispatch_fn(task))
                
                # If SequentialPolicy, we dispatch only one task at a time
                if isinstance(self.policy, SequentialPolicy):
                    break
            else:
                # Mark task BLOCKED if it isn't already
                await self.queue_manager.move_task(task.task_id, ExecutionQueueStatus.BLOCKED)
                logger.debug("Task blocked due to resource constraints", task_id=str(task.task_id))
