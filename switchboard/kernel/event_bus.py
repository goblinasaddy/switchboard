import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, TypeVar
from switchboard.interfaces.event_bus import IEventBus
from switchboard.interfaces.service import IService
from switchboard.types.common import BaseEvent
from switchboard.logging.config import get_logger

T = TypeVar("T", bound=BaseEvent)
logger = get_logger("event_bus")

class EventBus(IEventBus, IService):
    """
    Concrete implementation of the async IEventBus and IService interface.
    Coordinates event registration and concurrent propagation as a managed service.
    """

    def __init__(self) -> None:
        self._subscribers: dict[type[BaseEvent], set[Callable[[Any], Awaitable[None]]]] = defaultdict(set)

    @property
    def name(self) -> str:
        return "event_bus"

    @property
    def dependencies(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        logger.debug("Event Bus initialized")

    async def start(self) -> None:
        logger.debug("Event Bus started")

    async def shutdown(self) -> None:
        logger.debug("Event Bus shutting down")
        self._subscribers.clear()

    async def publish(self, event: BaseEvent) -> None:
        """
        Publish an event asynchronously. Dispatch to subscribers concurrently.
        
        Args:
            event: The event payload deriving from BaseEvent.
        """
        event_type = type(event)
        topic = event.topic

        # Find all handlers subscribed to this event or any of its parent classes
        target_handlers: list[Callable[[Any], Awaitable[None]]] = []
        for registered_type, handlers in self._subscribers.items():
            if issubclass(event_type, registered_type):
                target_handlers.extend(handlers)

        if not target_handlers:
            logger.debug("No subscribers registered for topic", topic=topic)
            return

        logger.debug(
            "Dispatching event", 
            topic=topic, 
            event_id=str(event.event_id), 
            subscribers=len(target_handlers)
        )

        # Build list of coroutines to execute in parallel
        tasks = [self._safe_dispatch(handler, event) for handler in target_handlers]
        await asyncio.gather(*tasks)

    async def _safe_dispatch(self, handler: Callable[[Any], Awaitable[None]], event: BaseEvent) -> None:
        """Execute a subscriber handler, swallowing and logging any raised exceptions."""
        try:
            await handler(event)
        except Exception as e:
            logger.exception(
                "Exception raised in event subscriber", 
                topic=event.topic, 
                handler=getattr(handler, "__name__", str(handler)),
                error=str(e)
            )

    async def subscribe(
        self, 
        event_type: type[T], 
        handler: Callable[[T], Awaitable[None]]
    ) -> None:
        """Subscribe an async callable to the specified event class type."""
        self._subscribers[event_type].add(handler)
        logger.debug(
            "Subscriber added", 
            event_type=event_type.__name__, 
            handler=getattr(handler, "__name__", str(handler))
        )

    async def unsubscribe(
        self, 
        event_type: type[T], 
        handler: Callable[[T], Awaitable[None]]
    ) -> None:
        """Remove a subscriber from the specified event class type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug(
                "Subscriber removed", 
                event_type=event_type.__name__, 
                handler=getattr(handler, "__name__", str(handler))
            )
            # Clean up key if empty
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
