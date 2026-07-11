from typing import AsyncIterator, Protocol, runtime_checkable
from switchboard.types.runtime import Model, ModelCapability, GenerationRequest, GenerationResponse

@runtime_checkable
class IProvider(Protocol):
    """
    Interface defining the operational contract for inference engine providers.
    All inference backends (Ollama, llama.cpp, etc.) must implement this interface.
    """

    @property
    def name(self) -> str:
        """Name of the provider backend."""
        ...

    async def initialize(self) -> None:
        """Initialize the connection to the inference backend."""
        ...

    async def shutdown(self) -> None:
        """Gracefully release provider resources."""
        ...

    async def health(self) -> bool:
        """Verify the health status of the provider backend."""
        ...

    async def capabilities(self) -> list[ModelCapability]:
        """List models' capabilities supported by this provider."""
        ...

    async def list_models(self) -> list[Model]:
        """Enumerate models offered by this provider."""
        ...

    async def load_model(self, name: str) -> None:
        """Load a model into VRAM/RAM memory."""
        ...

    async def unload_model(self, name: str) -> None:
        """Unload a model from VRAM/RAM memory."""
        ...

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute a complete generation request."""
        ...

    async def stream(self, request: GenerationRequest) -> AsyncIterator[GenerationResponse]:
        """Execute a streaming generation request."""
        ...

    async def interrupt(self) -> None:
        """Interrupt any current processing in this provider."""
        ...
