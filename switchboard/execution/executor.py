from uuid import UUID
from switchboard.task.workflow import Workflow
from switchboard.types.task import Task, TaskStatus
from switchboard.types.execution import ExecutionQueueStatus, WorkflowState
from switchboard.types.events import (
    WorkflowStartedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    TaskScheduledEvent,
)
from switchboard.interfaces.event_bus import IEventBus
from switchboard.execution.queues import QueueManager
from switchboard.logging.config import get_logger

logger = get_logger("workflow_executor")

class WorkflowExecutor:
    """
    Coordinates Workflow DAG walking, resolving dependency completions,
    and enqueuing newly ready downstream Tasks.
    """

    def __init__(self, queue_manager: QueueManager, event_bus: IEventBus | None = None) -> None:
        self.queue_manager = queue_manager
        self.event_bus = event_bus
        self._active_workflows: dict[str, Workflow] = {}
        self._states: dict[str, WorkflowState] = {}

    def get_workflow_state(self, name: str) -> WorkflowState | None:
        return self._states.get(name)

    async def submit_workflow(self, workflow: Workflow) -> None:
        """Submit a workflow, walk initial nodes, and enqueue ready tasks."""
        self._active_workflows[workflow.name] = workflow
        
        total_tasks = len(workflow.graph.nodes)
        state = WorkflowState(
            name=workflow.name,
            total_tasks=total_tasks,
            status="running"
        )
        self._states[workflow.name] = state
        
        logger.info("Starting workflow execution walk", workflow_name=workflow.name, tasks_count=total_tasks)
        if self.event_bus:
            await self.event_bus.publish(WorkflowStartedEvent(workflow.name))

        # Enqueue all initial tasks as WAITING first
        for node_id, data in workflow.graph.nodes(data=True):
            task: Task = data["task"]
            await self.queue_manager.enqueue(task, ExecutionQueueStatus.WAITING)

        # Resolve starting nodes (those with no parent dependencies)
        ready_tasks = workflow.get_ready_tasks()
        for task in ready_tasks:
            # Transition task to READY queue
            await self.queue_manager.move_task(task.task_id, ExecutionQueueStatus.READY)
            if self.event_bus:
                await self.event_bus.publish(TaskScheduledEvent(task.task_id, "ready"))

    async def process_task_completion(self, workflow_name: str, task_id: UUID, success: bool, error_msg: str | None = None) -> None:
        """Process task finish, update DAG states, and queue downstream tasks."""
        if workflow_name not in self._active_workflows:
            return
            
        workflow = self._active_workflows[workflow_name]
        state = self._states[workflow_name]
        
        # Retrieve and update node task status
        task = workflow.get_task(task_id)
        
        if success:
            task.status = TaskStatus.COMPLETED
            await self.queue_manager.move_task(task_id, ExecutionQueueStatus.COMPLETED)
            
            # Recalculate workflow state progress
            completed_count = sum(1 for _, d in workflow.graph.nodes(data=True) if d["task"].status == TaskStatus.COMPLETED)
            state.completed_tasks = completed_count
            state.progress_percentage = (completed_count / state.total_tasks) * 100.0
            
            # Resolve downstream nodes
            next_tasks = workflow.get_ready_tasks()
            for t in next_tasks:
                await self.queue_manager.move_task(t.task_id, ExecutionQueueStatus.READY)
                if self.event_bus:
                    await self.event_bus.publish(TaskScheduledEvent(t.task_id, "ready"))

            # Check if entire workflow completed
            if completed_count == state.total_tasks:
                state.status = "completed"
                logger.info("Workflow execution walk completed successfully", workflow_name=workflow.name)
                if self.event_bus:
                    await self.event_bus.publish(WorkflowCompletedEvent(workflow.name))
                # Cleanup active state reference
                self._active_workflows.pop(workflow_name, None)
        else:
            task.status = TaskStatus.FAILED
            await self.queue_manager.move_task(task_id, ExecutionQueueStatus.FAILED)
            state.status = "failed"
            
            logger.error("Workflow failed due to task execution failure", workflow_name=workflow.name, failed_task=str(task_id), error=error_msg)
            if self.event_bus:
                await self.event_bus.publish(WorkflowFailedEvent(workflow.name, error_msg or "Task failed."))
            
            # Terminate and cleanup active reference
            self._active_workflows.pop(workflow_name, None)

    async def cancel_workflow(self, workflow_name: str) -> None:
        """Cancel all tasks belonging to the target workflow."""
        if workflow_name not in self._active_workflows:
            return
            
        workflow = self._active_workflows[workflow_name]
        state = self._states[workflow_name]
        state.status = "failed"
        
        logger.info("Cancelling active workflow execution walk", workflow_name=workflow_name)
        
        # Stop and remove tasks
        for node_id, data in workflow.graph.nodes(data=True):
            task: Task = data["task"]
            if task.status in (TaskStatus.CREATED, TaskStatus.QUEUED, TaskStatus.RUNNING):
                task.status = TaskStatus.CANCELLED
                await self.queue_manager.move_task(task.task_id, ExecutionQueueStatus.FAILED)
                
        if self.event_bus:
            await self.event_bus.publish(WorkflowFailedEvent(workflow_name, "Cancelled by user."))
            
        self._active_workflows.pop(workflow_name, None)
