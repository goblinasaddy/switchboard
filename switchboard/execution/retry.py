import asyncio
from typing import Callable, Coroutine
from switchboard.interfaces.execution import IRetryManager
from switchboard.interfaces.event_bus import IEventBus
from switchboard.types.task import Task
from switchboard.types.events import RetryScheduledEvent
from switchboard.logging.config import get_logger

logger = get_logger("retry_manager")

class RetryManager(IRetryManager):
    """
    Manages task failure retries utilizing exponential backoff algorithms.
    """

    def __init__(self, base_delay_sec: float = 1.0, event_bus: IEventBus | None = None) -> None:
        self.base_delay_sec = base_delay_sec
        self.event_bus = event_bus

    def should_retry(self, task: Task) -> bool:
        """Check if task has retry attempts remaining."""
        return task.retry_count < task.max_retries

    def get_backoff_delay(self, task: Task) -> float:
        """Calculate wait delay in seconds using exponential backoff."""
        return self.base_delay_sec * (2.0 ** task.retry_count)

    async def schedule_retry(
        self,
        task: Task,
        retry_callback: Callable[[Task], Coroutine[None, None, None]]
    ) -> None:
        """Increment retry count, wait delay, and re-enqueue task for execution."""
        delay = self.get_backoff_delay(task)
        task.retry_count += 1
        
        logger.info(
            "Scheduling task retry", 
            task_id=str(task.task_id), 
            attempt=task.retry_count, 
            max_retries=task.max_retries,
            delay_sec=delay
        )
        
        if self.event_bus:
            await self.event_bus.publish(RetryScheduledEvent(task.task_id, task.retry_count, delay))

        # Run wait delay in background
        asyncio.create_task(self._wait_and_trigger(delay, task, retry_callback))

    async def _wait_and_trigger(
        self,
        delay: float,
        task: Task,
        callback: Callable[[Task], Coroutine[None, None, None]]
    ) -> None:
        await asyncio.sleep(delay)
        await callback(task)
