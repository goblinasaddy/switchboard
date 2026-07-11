import pytest
import time
from uuid import uuid4
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.types.task import (
    TaskContext,
    TaskStatus,
    TaskPriority,
    TaskResult,
    Artifact,
    ArtifactType,
)
from switchboard.task.workflow import Workflow
from switchboard.exceptions.base import SwitchBoardError
from switchboard.types.events import (
    TaskCreatedEvent,
    TaskQueuedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
)

def test_workflow_dependency_dag() -> None:
    # Set up DAG
    workflow = Workflow("Diag Workflow")
    
    context = TaskContext()
    
    # Instantiate Tasks
    from switchboard.types.task import Task
    task_a = Task(name="Task A", objective="Obj A", context_id=context.context_id)
    task_b = Task(name="Task B", objective="Obj B", context_id=context.context_id)
    task_c = Task(name="Task C", objective="Obj C", context_id=context.context_id)
    
    workflow.add_task(task_a)
    workflow.add_task(task_b)
    workflow.add_task(task_c)
    
    # B depends on A and C (A -> B, C -> B)
    workflow.add_dependency(task_a.task_id, task_b.task_id)
    workflow.add_dependency(task_c.task_id, task_b.task_id)
    
    # 1. At start, only A and C are ready (have no predecessors)
    ready = workflow.get_ready_tasks()
    ready_ids = {t.task_id for t in ready}
    assert len(ready) == 2
    assert ready_ids == {task_a.task_id, task_c.task_id}
    
    # 2. Simulate task A completes
    task_a.status = TaskStatus.COMPLETED
    ready = workflow.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].task_id == task_c.task_id
    
    # 3. Simulate task C completes
    task_c.status = TaskStatus.COMPLETED
    ready = workflow.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].task_id == task_b.task_id
    
    # 4. Simulate task B completes
    task_b.status = TaskStatus.COMPLETED
    ready = workflow.get_ready_tasks()
    assert len(ready) == 0


@pytest.mark.asyncio
async def test_task_manager_transitions_and_events() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    event_bus = kernel.get_service("event_bus")
    task_manager = kernel.get_service("task_manager")
    
    # Track events
    events = []
    async def log_event(event) -> None:
        events.append(event)
        
    await event_bus.subscribe(TaskCreatedEvent, log_event)
    await event_bus.subscribe(TaskQueuedEvent, log_event)
    await event_bus.subscribe(TaskStartedEvent, log_event)
    await event_bus.subscribe(TaskCompletedEvent, log_event)
    
    # Create task
    context = TaskContext(repository_root="/tmp/repo")
    task = await task_manager.create_task(
        name="Test Task",
        objective="Run tests",
        context=context,
        priority=TaskPriority.HIGH
    )
    assert task.status == TaskStatus.CREATED
    assert task.priority == TaskPriority.HIGH
    
    # Submit task
    await task_manager.submit_task(task.task_id)
    assert task.status == TaskStatus.QUEUED
    
    # Cannot complete immediately
    with pytest.raises(SwitchBoardError):
        await task_manager.complete_task(task.task_id, TaskResult(status=TaskStatus.COMPLETED))
        
    # Start task
    await task_manager.start_task(task.task_id)
    assert task.status == TaskStatus.RUNNING
    
    # Complete task with a first-class Artifact!
    artifact = Artifact(name="patch.diff", type=ArtifactType.PATCH, path="/tmp/patch.diff")
    result = TaskResult(
        status=TaskStatus.COMPLETED,
        artifacts=[artifact],
        execution_time_ms=120.0
    )
    await task_manager.complete_task(task.task_id, result)
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None
    assert task.result.artifacts[0].name == "patch.diff"
    assert task.result.artifacts[0].type == ArtifactType.PATCH
    
    # Check event triggers
    event_types = [type(e) for e in events]
    assert TaskCreatedEvent in event_types
    assert TaskQueuedEvent in event_types
    assert TaskStartedEvent in event_types
    assert TaskCompletedEvent in event_types
    
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_task_manager_cancellation() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    
    task_manager = kernel.get_service("task_manager")
    
    context = TaskContext()
    task = await task_manager.create_task("Cancel Task", "Should get cancelled", context)
    
    # Submit and start
    await task_manager.submit_task(task.task_id)
    await task_manager.start_task(task.task_id)
    
    # Cancel
    await task_manager.cancel_task(task.task_id)
    assert task.status == TaskStatus.CANCELLED
    assert task.finished_at is not None
    
    await kernel.shutdown()
