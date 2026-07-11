from typing import Any, AsyncIterator
from uuid import UUID, uuid4
from switchboard.interfaces.compute import IComputeSession
from switchboard.interfaces.provider import IProvider
from switchboard.interfaces.event_bus import IEventBus
from switchboard.types.runtime import GenerationRequest, GenerationResponse
from switchboard.types.events import (
    GenerationStartedEvent,
    GenerationCompletedEvent,
    GenerationFailedEvent,
)
from switchboard.logging.config import get_logger

logger = get_logger("compute_session")

class ComputeSession(IComputeSession):
    """
    Concrete implementation of IComputeSession representing an isolated prompt execution scope.
    """

    def __init__(self, model_name: str, provider: IProvider, event_bus: IEventBus | None = None) -> None:
        self._session_id = uuid4()
        self._model_name = model_name
        self._provider = provider
        self._event_bus = event_bus
        self._history: list[dict[str, Any]] = []

    @property
    def session_id(self) -> UUID:
        return self._session_id

    @property
    def active_model(self) -> str | None:
        return self._model_name

    async def get_history(self) -> list[Any]:
        return self._history

    async def execute(self, request: GenerationRequest) -> GenerationResponse:
        """Execute request using underlying provider and log context events."""
        # Inject trace tags
        request.metadata["model_name"] = self._model_name
        request.metadata["session_id"] = str(self._session_id)

        if self._event_bus:
            await self._event_bus.publish(GenerationStartedEvent(self._session_id, self._model_name))

        try:
            response = await self._provider.generate(request)
            
            # Record execution trace
            self._history.append({
                "request": request.model_dump(),
                "response": response.model_dump()
            })

            if self._event_bus:
                await self._event_bus.publish(
                    GenerationCompletedEvent(
                        self._session_id, 
                        self._model_name, 
                        response.token_usage.get("total_tokens", 0)
                    )
                )
            return response

        except Exception as e:
            logger.error("Session execution failed", session_id=str(self._session_id), error=str(e))
            if self._event_bus:
                await self._event_bus.publish(GenerationFailedEvent(self._session_id, self._model_name, str(e)))
            raise

    async def execute_stream(self, request: GenerationRequest) -> AsyncIterator[GenerationResponse]:
        """Execute request streaming outputs and log context events."""
        request.metadata["model_name"] = self._model_name
        request.metadata["session_id"] = str(self._session_id)

        if self._event_bus:
            await self._event_bus.publish(GenerationStartedEvent(self._session_id, self._model_name))

        try:
            stream_iter = await self._provider.stream(request)
        except Exception as e:
            if self._event_bus:
                await self._event_bus.publish(GenerationFailedEvent(self._session_id, self._model_name, str(e)))
            raise

        async def stream_wrapper() -> AsyncIterator[GenerationResponse]:
            last_response = None
            try:
                async for chunk in stream_iter:
                    last_response = chunk
                    yield chunk

                # Capture final state when generator completes
                if last_response:
                    self._history.append({
                        "request": request.model_dump(),
                        "response": last_response.model_dump()
                    })
                    if self._event_bus:
                        await self._event_bus.publish(
                            GenerationCompletedEvent(
                                self._session_id, 
                                self._model_name, 
                                last_response.token_usage.get("total_tokens", 0)
                            )
                        )
            except Exception as e:
                logger.error("Session execution stream failed", session_id=str(self._session_id), error=str(e))
                if self._event_bus:
                    await self._event_bus.publish(GenerationFailedEvent(self._session_id, self._model_name, str(e)))
                raise

        return stream_wrapper()

    async def cancel(self) -> None:
        """Interrupt active execution loops."""
        logger.info("Cancellation invoked on session", session_id=str(self._session_id))
        await self._provider.interrupt()
