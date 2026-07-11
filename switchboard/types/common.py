from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    """
    Base event class for all system-wide communication in SwitchBoard.
    
    All published events must inherit from this model to ensure consistency 
    for trace-logging, serialisation, and eventual distributed routing.
    """
    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp in UTC when the event was generated."
    )
    sender: str = Field(default="system", description="Identifier of the publishing subsystem.")
    payload: dict[str, Any] = Field(
        default_factory=dict, 
        description="Structured key-value payload containing event-specific data."
    )

    @property
    def topic(self) -> str:
        """
        The event topic name, derived automatically from the class name.
        Can be overridden in subclasses for custom routing.
        """
        return self.__class__.__name__
