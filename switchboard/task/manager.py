import time
from uuid import UUID
from switchboard.interfaces.task import ITaskManager
from switchboard.interfaces.service import IService
from switchboard.interfaces.event_bus import IEventBus
from switchboard.types.task import Task, TaskContext, TaskStatus, TaskPriority, TaskResult
from switchboard.types.events import (
    TaskCreatedEvent,
    TaskQueuedEvent,
    TaskStartedEvent,
    TaskPausedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskCancelledEvent,
)
from switchboard.logging.config import get_logger
from switchboard.exceptions.base import SwitchBoardError

logger = get_logger("task_manager")

class TaskManager(ITaskManager, IService):
    """
    Subsystem coordinator managing task creation, status state machines,
    event triggers, and context registrations.
    """

    def __init__(self, event_bus: IEventBus | None = None) -> None:
        self._event_bus = event_bus
        self._tasks: dict[UUID, Task] = {}
        self._contexts: dict[UUID, TaskContext] = {}

    @property
    def name(self) -> str:
        return "task_manager"

    @property
    def dependencies(self) -> list[str]:
        return ["event_bus"]

    async def initialize(self) -> None:
        logger.info("Initializing Task Manager")
        self._tasks.clear()
        self._contexts.clear()

    async def start(self) -> None:
        logger.info("Task Manager started")

    async def shutdown(self) -> None:
        logger.info("Shutting down Task Manager")
        self._tasks.clear()
        self._contexts.clear()

    # ITaskManager Interface

    async def create_task(
        self,
        name: str,
        objective: str,
        context: TaskContext,
        priority: TaskPriority = TaskPriority.DEFAULT
    ) -> Task:
        """Create a new Task registration record."""
        # 1. Register context
        self._contexts[context.context_id] = context
        
        # 2. Build task
        task = Task(
            name=name,
            objective=objective,
            context_id=context.context_id,
            priority=priority,
            created_at=time.time()
        )
        self._tasks[task.task_id] = task
        
        logger.info("Created Task", task_id=str(task.task_id), task_name=name)
        if self._event_bus:
            await self._event_bus.publish(TaskCreatedEvent(task.task_id, name))
            
        return task

    async def submit_task(self, task_id: UUID) -> None:
        """Submit task to scheduler queue."""
        task = await self.get_task(task_id)
        if task.status != TaskStatus.CREATED:
            raise SwitchBoardError(f"Cannot submit task '{task_id}' in state '{task.status.value}'.")
            
        task.status = TaskStatus.QUEUED
        logger.info("Queued Task", task_id=str(task_id))
        
        if self._event_bus:
            await self._event_bus.publish(TaskQueuedEvent(task_id))

    async def get_task(self, task_id: UUID) -> Task:
        """Retrieve task by its UUID."""
        if task_id not in self._tasks:
            raise SwitchBoardError(f"Task '{task_id}' not found.")
        return self._tasks[task_id]

    async def cancel_task(self, task_id: UUID) -> None:
        """Interrupt and cancel a task execution."""
        task = await self.get_task(task_id)
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            logger.warning("Attempted to cancel task already in terminal state", task_id=str(task_id), status=task.status.value)
            return
            
        task.status = TaskStatus.CANCELLED
        task.finished_at = time.time()
        
        logger.info("Cancelled Task", task_id=str(task_id))
        if self._event_bus:
            await self._event_bus.publish(TaskCancelledEvent(task_id))

    # Auxiliary transition helpers (to be used by Scheduler/Engine coordinators)

    async def start_task(self, task_id: UUID) -> None:
        """Transition task from QUEUED to RUNNING."""
        task = await self.get_task(task_id)
        if task.status not in (TaskStatus.QUEUED, TaskStatus.PAUSED):
            raise SwitchBoardError(f"Cannot start task '{task_id}' in state '{task.status.value}'.")
            
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        logger.info("Started Task running", task_id=str(task_id))
        if self._event_bus:
            await self._event_bus.publish(TaskStartedEvent(task_id))

    async def pause_task(self, task_id: UUID) -> None:
        """Transition task to PAUSED state."""
        task = await self.get_task(task_id)
        if task.status != TaskStatus.RUNNING:
            raise SwitchBoardError(f"Cannot pause task '{task_id}' in state '{task.status.value}'.")
            
        task.status = TaskStatus.PAUSED
        logger.info("Paused Task", task_id=str(task_id))
        if self._event_bus:
            await self._event_bus.publish(TaskPausedEvent(task_id))

    async def complete_task(self, task_id: UUID, result: TaskResult) -> None:
        """Transition task to COMPLETED state and attach execution result."""
        task = await self.get_task(task_id)
        if task.status != TaskStatus.RUNNING:
            raise SwitchBoardError(f"Cannot complete task '{task_id}' in state '{task.status.value}'.")
            
        task.status = TaskStatus.COMPLETED
        task.finished_at = time.time()
        task.result = result
        
        logger.info("Completed Task successfully", task_id=str(task_id))
        if self._event_bus:
            await self._event_bus.publish(TaskCompletedEvent(task_id, success=True))

    async def fail_task(self, task_id: UUID, error: str) -> None:
        """Transition task to FAILED state and capture error description."""
        task = await self.get_task(task_id)
        if task.status != TaskStatus.RUNNING:
            raise SwitchBoardError(f"Cannot fail task '{task_id}' in state '{task.status.value}'.")
            
        task.status = TaskStatus.FAILED
        task.finished_at = time.time()
        task.result = TaskResult(
            status=TaskStatus.FAILED,
            error=error
        )
        
        logger.error("Failed Task execution", task_id=str(task_id), error=error)
        if self._event_bus:
            await self._event_bus.publish(TaskFailedEvent(task_id, error))
