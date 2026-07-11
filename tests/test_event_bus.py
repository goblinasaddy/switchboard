import pytest
from switchboard.types.common import BaseEvent
from switchboard.kernel.event_bus import EventBus

class CustomTestEvent(BaseEvent):
    pass

class DerivedTestEvent(CustomTestEvent):
    pass

@pytest.mark.asyncio
async def test_event_bus_pub_sub() -> None:
    bus = EventBus()
    received = []

    async def my_handler(event: CustomTestEvent) -> None:
        received.append(event)

    # Subscribe and publish
    await bus.subscribe(CustomTestEvent, my_handler)
    event = CustomTestEvent(payload={"data": "payload_test"})
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].event_id == event.event_id
    assert received[0].payload["data"] == "payload_test"


@pytest.mark.asyncio
async def test_event_bus_unsubscribe() -> None:
    bus = EventBus()
    received = []

    async def my_handler(event: CustomTestEvent) -> None:
        received.append(event)

    await bus.subscribe(CustomTestEvent, my_handler)
    await bus.unsubscribe(CustomTestEvent, my_handler)

    event = CustomTestEvent()
    await bus.publish(event)

    # Handler shouldn't run after unsubscribe
    assert len(received) == 0


@pytest.mark.asyncio
async def test_event_bus_inheritance_matching() -> None:
    bus = EventBus()
    received = []

    async def parent_handler(event: CustomTestEvent) -> None:
        received.append(event)

    # Subscribing to base class should capture derived classes too
    await bus.subscribe(CustomTestEvent, parent_handler)
    
    derived_event = DerivedTestEvent()
    await bus.publish(derived_event)

    assert len(received) == 1
    assert received[0].event_id == derived_event.event_id


@pytest.mark.asyncio
async def test_event_bus_error_isolation() -> None:
    bus = EventBus()
    successful_runs = []

    async def failing_handler(event: CustomTestEvent) -> None:
        raise ValueError("Simulated handler crash")

    async def working_handler(event: CustomTestEvent) -> None:
        successful_runs.append(event)

    await bus.subscribe(CustomTestEvent, failing_handler)
    await bus.subscribe(CustomTestEvent, working_handler)

    event = CustomTestEvent()
    # Should complete without raising value error out of publish call
    await bus.publish(event)

    assert len(successful_runs) == 1
    assert successful_runs[0].event_id == event.event_id
