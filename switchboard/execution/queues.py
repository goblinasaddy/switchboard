import asyncio
from uuid import UUID
from switchboard.types.task import Task
from switchboard.types.execution import ExecutionQueueStatus, ExecutionQueueState

class QueueManager:
    """
    Manages task execution queue structures in a thread-safe, memory-only registry.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._tasks: dict[UUID, Task] = {}
        self._queues: dict[ExecutionQueueStatus, list[UUID]] = {
            ExecutionQueueStatus.WAITING: [],
            ExecutionQueueStatus.READY: [],
            ExecutionQueueStatus.RUNNING: [],
            ExecutionQueueStatus.BLOCKED: [],
            ExecutionQueueStatus.COMPLETED: [],
            ExecutionQueueStatus.FAILED: []
        }

    async def enqueue(self, task: Task, status: ExecutionQueueStatus) -> None:
        """Add a Task to the registry and place it in the target status queue."""
        async with self._lock:
            self._tasks[task.task_id] = task
            # Remove from any existing queue
            for q_list in self._queues.values():
                if task.task_id in q_list:
                    q_list.remove(task.task_id)
            self._queues[status].append(task.task_id)

    async def move_task(self, task_id: UUID, to_status: ExecutionQueueStatus) -> None:
        """Transition a task's queue state."""
        async with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task '{task_id}' not managed by QueueManager.")
            
            # Remove from old queue
            for q_list in self._queues.values():
                if task_id in q_list:
                    q_list.remove(task_id)
            
            # Add to new queue
            self._queues[to_status].append(task_id)

    async def get_tasks_in_queue(self, status: ExecutionQueueStatus) -> list[Task]:
        """Get all Tasks currently assigned to a target status queue."""
        async with self._lock:
            return [self._tasks[tid] for tid in self._queues[status] if tid in self._tasks]

    async def get_task(self, task_id: UUID) -> Task | None:
        """Get a single task."""
        async with self._lock:
            return self._tasks.get(task_id)

    async def remove_task(self, task_id: UUID) -> None:
        """Remove a task from all queues."""
        async with self._lock:
            self._tasks.pop(task_id, None)
            for q_list in self._queues.values():
                if task_id in q_list:
                    q_list.remove(task_id)

    async def get_queue_state(self) -> ExecutionQueueState:
        """Compile a snapshot of the current queue state."""
        async with self._lock:
            active_vram = 0.0
            for tid in self._queues[ExecutionQueueStatus.RUNNING]:
                task = self._tasks.get(tid)
                if task:
                    active_vram += task.requirements.estimated_vram_gb
                    
            return ExecutionQueueState(
                waiting_count=len(self._queues[ExecutionQueueStatus.WAITING]),
                ready_count=len(self._queues[ExecutionQueueStatus.READY]),
                running_count=len(self._queues[ExecutionQueueStatus.RUNNING]),
                blocked_count=len(self._queues[ExecutionQueueStatus.BLOCKED]),
                completed_count=len(self._queues[ExecutionQueueStatus.COMPLETED]),
                failed_count=len(self._queues[ExecutionQueueStatus.FAILED]),
                active_vram_allocated_gb=active_vram
            )
