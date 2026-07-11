import pytest
import asyncio
from uuid import uuid4
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.types.task import Task, TaskContext, TaskStatus, TaskPriority, TaskResult, ResourceRequirements
from switchboard.types.execution import ExecutionQueueStatus
from switchboard.task.workflow import Workflow
from switchboard.execution.scheduler import PriorityVRAMPolicy, FIFOPolicy, SequentialPolicy

@pytest.mark.asyncio
async def test_scheduler_priority_sorting() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    execution_engine = kernel.get_service("execution_engine")
    task_manager = kernel.get_service("task_manager")
    
    context = TaskContext()
    
    # Create tasks with different priorities
    task_low = await task_manager.create_task("Low Priority", "low", context, priority=TaskPriority.LOW)
    task_high = await task_manager.create_task("High Priority", "high", context, priority=TaskPriority.HIGH)
    task_critical = await task_manager.create_task("Critical Priority", "crit", context, priority=TaskPriority.CRITICAL)
    
    # Move them to ready queue
    await execution_engine.queue_manager.enqueue(task_low, ExecutionQueueStatus.READY)
    await execution_engine.queue_manager.enqueue(task_high, ExecutionQueueStatus.READY)
    await execution_engine.queue_manager.enqueue(task_critical, ExecutionQueueStatus.READY)
    
    # Pluggable scheduling policy sorts them
    policy = PriorityVRAMPolicy()
    ready = [task_low, task_high, task_critical]
    sorted_tasks = policy.sort_tasks(ready)
    
    # Assert Critical -> High -> Low
    assert sorted_tasks[0].task_id == task_critical.task_id
    assert sorted_tasks[1].task_id == task_high.task_id
    assert sorted_tasks[2].task_id == task_low.task_id
    
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_resource_constraint_blocking_and_dispatch() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    task_manager = kernel.get_service("task_manager")
    
    # Set VRAM limit to 8.0 GB for testing
    from switchboard.execution.manager import ExecutionEngine
    execution_engine = ExecutionEngine(
        task_manager=task_manager,
        event_bus=kernel.get_service("event_bus"),
        max_vram_gb=8.0
    )
    await execution_engine.initialize()
    await execution_engine.start()
    
    context = TaskContext()
    
    # Task A: requires 6GB VRAM
    task_a = await task_manager.create_task("Task A", "6gb", context, priority=TaskPriority.HIGH)
    task_a.requirements = ResourceRequirements(estimated_vram_gb=6.0)
    
    # Task B: requires 4GB VRAM
    task_b = await task_manager.create_task("Task B", "4gb", context, priority=TaskPriority.LOW)
    task_b.requirements = ResourceRequirements(estimated_vram_gb=4.0)
    
    # Custom mock execution trackers
    completed_tasks = []
    
    async def run_mock_task(task: Task) -> TaskResult:
        await asyncio.sleep(0.05)
        completed_tasks.append(task.task_id)
        return TaskResult(status=TaskStatus.COMPLETED)
        
    execution_engine.register_task_executor(task_a.task_id, run_mock_task)
    execution_engine.register_task_executor(task_b.task_id, run_mock_task)
    
    # Submit tasks to set status to QUEUED in task manager
    await task_manager.submit_task(task_a.task_id)
    await task_manager.submit_task(task_b.task_id)
    
    # Enqueue both as READY
    await execution_engine.queue_manager.enqueue(task_a, ExecutionQueueStatus.READY)
    await execution_engine.queue_manager.enqueue(task_b, ExecutionQueueStatus.READY)
    
    # Trigger scheduler pass
    await execution_engine.scheduler.schedule()
    
    # Task A should start because 6GB <= 8GB. Task B should block because 6GB + 4GB > 8GB.
    state = await execution_engine.queue_manager.get_queue_state()
    assert state.running_count == 1
    assert state.blocked_count == 1
    
    # Wait for Task A to complete
    await asyncio.sleep(0.1)
    
    # Check that Task B was unblocked and dispatched once Task A released its resources
    state = await execution_engine.queue_manager.get_queue_state()
    assert task_a.task_id in completed_tasks
    
    # Eventually B should complete too
    await asyncio.sleep(0.1)
    assert task_b.task_id in completed_tasks
    
    await execution_engine.shutdown()
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_workflow_dag_executor_run() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    execution_engine = kernel.get_service("execution_engine")
    task_manager = kernel.get_service("task_manager")
    
    context = TaskContext()
    workflow = Workflow("Linear Flow")
    
    # Create linear workflow: A -> B
    task_a = await task_manager.create_task("A", "start", context)
    task_b = await task_manager.create_task("B", "finish", context)
    
    workflow.add_task(task_a)
    workflow.add_task(task_b)
    workflow.add_dependency(task_a.task_id, task_b.task_id)
    
    # Submit workflow
    await execution_engine.submit_workflow(workflow)
    
    # Initially Task A should be RUNNING or completed, Task B is WAITING or READY
    await asyncio.sleep(0.1)
    
    # Wait for completion of entire workflow
    await asyncio.sleep(0.2)
    
    # Assert both tasks completed successfully
    assert task_a.status == TaskStatus.COMPLETED
    assert task_b.status == TaskStatus.COMPLETED
    
    state = execution_engine.workflow_executor.get_workflow_state("Linear Flow")
    assert state is not None
    assert state.status == "completed"
    assert state.progress_percentage == 100.0
    
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_retry_manager_backoff() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    execution_engine = kernel.get_service("execution_engine")
    task_manager = kernel.get_service("task_manager")
    
    context = TaskContext()
    task = await task_manager.create_task("Failing Task", "fail", context)
    task.max_retries = 2
    
    # Custom executor that throws exception to trigger retry
    run_count = 0
    async def run_fail(t: Task) -> TaskResult:
        nonlocal run_count
        run_count += 1
        raise ValueError("Simulated Task Failure")
        
    execution_engine.register_task_executor(task.task_id, run_fail)
    
    # Submit task to transition state to QUEUED in task manager
    await task_manager.submit_task(task.task_id)
    
    # Enqueue and trigger schedule
    await execution_engine.queue_manager.enqueue(task, ExecutionQueueStatus.READY)
    await execution_engine.scheduler.schedule()
    
    # Task should run, fail, retry 1 (delay 0.2s), retry 2 (delay 0.4s), then fail
    await asyncio.sleep(0.1)  # Run 1 fails
    assert task.retry_count == 1
    
    await asyncio.sleep(0.3)  # Run 2 fails (delay 0.2s)
    assert task.retry_count == 2
    
    await asyncio.sleep(0.5)  # Run 3 fails (delay 0.4s) -> exhausts retries
    assert task.status == TaskStatus.FAILED
    assert run_count == 3
    
    await kernel.shutdown()
