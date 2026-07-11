from typing import Any, Awaitable, Callable, Protocol, TypeVar, runtime_checkable
from switchboard.types.common import BaseEvent

T = TypeVar("T", bound=BaseEvent)

@runtime_checkable
class IEventBus(Protocol):
    """
    Interface defining the subscription and propagation model for system-wide events.
    """

    async def publish(self, event: BaseEvent) -> None:
        """
        Publish an event asynchronously to all registered subscribers.
        
        Args:
            event: The event instance to propagate, inheriting from BaseEvent.
        """
        ...

    async def subscribe(
        self, 
        event_type: type[T], 
        handler: Callable[[T], Awaitable[None]]
    ) -> None:
        """
        Subscribe a handler callback to a specific event type.
        
        Args:
            event_type: The class of the event to listen for.
            handler: A coroutine function invoked when the event is published.
        """
        ...

    async def unsubscribe(
        self, 
        event_type: type[T], 
        handler: Callable[[T], Awaitable[None]]
    ) -> None:
        """
        Unsubscribe a handler callback from a specific event type.
        
        Args:
            event_type: The class of the event to stop listening for.
            handler: The registered callback to remove.
        """
        ...
