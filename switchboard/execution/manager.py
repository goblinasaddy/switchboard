import asyncio
from uuid import UUID
from typing import Callable, Coroutine
from switchboard.interfaces.execution import IExecutionEngine, ISchedulingPolicy
from switchboard.interfaces.service import IService
from switchboard.interfaces.event_bus import IEventBus
from switchboard.interfaces.task import ITaskManager
from switchboard.types.task import Task, TaskStatus, TaskResult
from switchboard.types.execution import ExecutionQueueStatus
from switchboard.types.events import ResourcesReleasedEvent
from switchboard.task.workflow import Workflow
from switchboard.execution.queues import QueueManager
from switchboard.execution.allocator import ResourceAllocator
from switchboard.execution.scheduler import Scheduler, PriorityVRAMPolicy
from switchboard.execution.executor import WorkflowExecutor
from switchboard.execution.retry import RetryManager
from switchboard.execution.monitor import ExecutionMonitor
from switchboard.logging.config import get_logger

logger = get_logger("execution_engine")

class ExecutionEngine(IExecutionEngine, IService):
    """
    Subsystem coordinator orchestrating the Execution Engine loop algorithm:
    Workflow -> Resolve Ready -> Scheduling Strategy -> Resource Lock -> Dispatch -> Complete -> Release.
    """

    def __init__(
        self,
        task_manager: ITaskManager,
        event_bus: IEventBus | None = None,
        policy: ISchedulingPolicy | None = None,
        max_vram_gb: float = 12.0,
        max_ram_gb: float = 16.0
    ) -> None:
        self._task_manager = task_manager
        self._event_bus = event_bus
        
        # 1. Instantiate engine components
        self.queue_manager = QueueManager()
        self.resource_allocator = ResourceAllocator(max_vram_gb, max_ram_gb)
        self.retry_manager = RetryManager(base_delay_sec=0.1, event_bus=event_bus)
        self.workflow_executor = WorkflowExecutor(self.queue_manager, event_bus)
        self.monitor = ExecutionMonitor(self.queue_manager, self.resource_allocator)
        
        self.policy = policy or PriorityVRAMPolicy()
        self.scheduler = Scheduler(
            queue_manager=self.queue_manager,
            resource_allocator=self.resource_allocator,
            policy=self.policy,
            dispatch_fn=self._dispatch_task,
            event_bus=event_bus
        )
        
        # Maps active task ID to its workflow name
        self._task_workflow_map: dict[UUID, str] = {}
        # Plug custom executors for tasks (can be set for integrations)
        self._task_executors: dict[UUID, Callable[[Task], Coroutine[None, None, TaskResult]]] = {}

    @property
    def name(self) -> str:
        return "execution_engine"

    @property
    def dependencies(self) -> list[str]:
        return ["event_bus", "task_manager"]

    async def initialize(self) -> None:
        logger.info("Initializing Execution Engine")
        self._task_workflow_map.clear()
        self._task_executors.clear()
        await self.queue_manager.enqueue(Task(name="placeholder", objective="", context_id=UUID(int=0)), ExecutionQueueStatus.COMPLETED)
        await self.queue_manager.remove_task(UUID(int=0))

    async def start(self) -> None:
        logger.info("Execution Engine started")

    async def shutdown(self) -> None:
        logger.info("Shutting down Execution Engine")

    # Public IExecutionEngine Interface

    async def submit_workflow(self, workflow: Workflow) -> None:
        """Submit a Workflow DAG to the execution loops."""
        # Record task-to-workflow mapping for completions resolution
        for node_id, data in workflow.graph.nodes(data=True):
            self._task_workflow_map[node_id] = workflow.name
            task = data["task"]
            if task.status == TaskStatus.CREATED:
                await self._task_manager.submit_task(task.task_id)
            
        await self.workflow_executor.submit_workflow(workflow)
        
        # Trigger initial scheduling pass
        await self.scheduler.schedule()

    async def cancel_workflow(self, workflow_name: str) -> None:
        """Cancel all active/pending tasks for a workflow."""
        await self.workflow_executor.cancel_workflow(workflow_name)
        # Release allocations for canceled tasks
        for tid, wname in list(self._task_workflow_map.items()):
            if wname == workflow_name:
                self.resource_allocator.release(tid)
                self._task_workflow_map.pop(tid, None)

    # Custom Executor Hooks (for testing and integrations)

    def register_task_executor(self, task_id: UUID, run_fn: Callable[[Task], Coroutine[None, None, TaskResult]]) -> None:
        """Register a custom asynchronous execution runner for a specific task."""
        self._task_executors[task_id] = run_fn

    # Core Dispatch Loop Implementation

    async def _dispatch_task(self, task: Task) -> None:
        """Core asynchronous dispatch runner for executing a task."""
        logger.info("Dispatching task execution block", task_id=str(task.task_id), task_name=task.name)
        
        # Transition state in task manager
        # Since Scheduler already moves it to RUNNING in the queue manager, we align the task manager state here
        await self._task_manager.start_task(task.task_id)
        
        try:
            # Check if custom runner is defined, otherwise default to a mock async generator run
            if task.task_id in self._task_executors:
                result = await self._task_executors[task.task_id](task)
            else:
                # Default mock execution (simulates compute generation time)
                await asyncio.sleep(0.05)
                result = TaskResult(
                    status=TaskStatus.COMPLETED,
                    execution_time_ms=50.0
                )
            
            await self._complete_task(task, result)
            
        except Exception as ex:
            logger.error("Error executing task block", task_id=str(task.task_id), error=str(ex))
            await self._fail_task(task, str(ex))

    async def _complete_task(self, task: Task, result: TaskResult) -> None:
        """Process successful task completion."""
        # 1. Release locked resource constraints
        self.resource_allocator.release(task.task_id)
        if self._event_bus:
            await self._event_bus.publish(ResourcesReleasedEvent(task.task_id))
            
        # 2. Mark completed in task manager
        await self._task_manager.complete_task(task.task_id, result)
        
        # 3. Inform workflow executor to walk next nodes
        workflow_name = self._task_workflow_map.get(task.task_id)
        if workflow_name:
            await self.workflow_executor.process_task_completion(workflow_name, task.task_id, success=True)
            
        # 4. Trigger scheduler tick to dispatch next ready tasks
        await self.scheduler.schedule()

    async def _fail_task(self, task: Task, error_msg: str) -> None:
        """Process task failure and trigger retry manager."""
        # 1. Release locked resources immediately
        self.resource_allocator.release(task.task_id)
        if self._event_bus:
            await self._event_bus.publish(ResourcesReleasedEvent(task.task_id))

        # 2. Ask RetryManager if we can retry
        if self.retry_manager.should_retry(task):
            await self.retry_manager.schedule_retry(task, self._retry_task_callback)
        else:
            # Retries exhausted, mark failed in task manager and workflow executor
            await self._task_manager.fail_task(task.task_id, error_msg)
            
            workflow_name = self._task_workflow_map.get(task.task_id)
            if workflow_name:
                await self.workflow_executor.process_task_completion(
                    workflow_name, 
                    task.task_id, 
                    success=False, 
                    error_msg=error_msg
                )
                
            # Trigger scheduler pass to dispatch remaining branches
            await self.scheduler.schedule()

    async def _retry_task_callback(self, task: Task) -> None:
        """Callback from RetryManager to re-submit a task to READY queue."""
        # Reset task status to QUEUED in task manager
        # Since task manager start_task transitions from QUEUED/PAUSED, we re-submit it
        task.status = TaskStatus.CREATED
        await self._task_manager.submit_task(task.task_id)
        
        # Move back to READY in QueueManager
        await self.queue_manager.move_task(task.task_id, ExecutionQueueStatus.READY)
        
        # Trigger scheduling tick
        await self.scheduler.schedule()
