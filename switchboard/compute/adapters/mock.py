import asyncio
import time
from typing import AsyncIterator
from switchboard.interfaces.provider import IProvider
from switchboard.types.runtime import Model, ModelCapability, ModelStatus, GenerationRequest, GenerationResponse
from switchboard.exceptions.base import SwitchBoardError
from switchboard.logging.config import get_logger

logger = get_logger("mock_provider")

class MockProvider(IProvider):
    """
    Simulated implementation of IProvider to enable testing and dry-runs
    without requiring active inference engines (like Ollama).
    """

    def __init__(self) -> None:
        self._initialized = False
        self._interrupted = False
        self._models = {
            "mock-llama3": Model(
                name="mock-llama3",
                provider="mock",
                family="llama",
                quantization="Q4_K_M",
                context_length=8192,
                estimated_vram_gb=4.5,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING],
                status=ModelStatus.UNLOADED
            ),
            "mock-mistral": Model(
                name="mock-mistral",
                provider="mock",
                family="mistral",
                quantization="FP16",
                context_length=32768,
                estimated_vram_gb=14.0,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.STREAMING, ModelCapability.TOOLS],
                status=ModelStatus.UNLOADED
            )
        }

    @property
    def name(self) -> str:
        return "mock"

    async def initialize(self) -> None:
        logger.info("Initializing Mock Provider")
        self._initialized = True

    async def shutdown(self) -> None:
        logger.info("Shutting down Mock Provider")
        for m in self._models.values():
            m.status = ModelStatus.UNLOADED
        self._initialized = False

    async def health(self) -> bool:
        return self._initialized

    async def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.CHAT,
            ModelCapability.STREAMING,
            ModelCapability.TOOLS
        ]

    async def list_models(self) -> list[Model]:
        if not self._initialized:
            raise SwitchBoardError("Mock provider is not initialized.")
        return list(self._models.values())

    async def load_model(self, name: str) -> None:
        if not self._initialized:
            raise SwitchBoardError("Mock provider is not initialized.")
        if name not in self._models:
            raise SwitchBoardError(f"Model '{name}' not supported by Mock provider.")
        
        logger.info("Loading mock model", model=name)
        self._models[name].status = ModelStatus.LOADING
        await asyncio.sleep(0.5)  # simulate loading delay
        self._models[name].status = ModelStatus.LOADED
        logger.info("Mock model loaded successfully", model=name)

    async def unload_model(self, name: str) -> None:
        if not self._initialized:
            raise SwitchBoardError("Mock provider is not initialized.")
        if name not in self._models:
            raise SwitchBoardError(f"Model '{name}' not supported by Mock provider.")
        
        logger.info("Unloading mock model", model=name)
        self._models[name].status = ModelStatus.UNLOADED

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self._initialized:
            raise SwitchBoardError("Mock provider is not initialized.")
        
        # Check active model (simulate loading if unloaded)
        model_name = request.metadata.get("model_name", "mock-llama3")
        if model_name not in self._models:
            raise SwitchBoardError(f"Model '{model_name}' not found.")
        
        model_obj = self._models[model_name]
        if model_obj.status != ModelStatus.LOADED:
            await self.load_model(model_name)

        start_time = time.perf_counter()
        self._interrupted = False

        prompt = request.inputs.get("prompt", "")
        # Simulated response logic
        response_text = f"Simulated output response for prompt: '{prompt}' using mock model: {model_name}"
        
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        latency = (time.perf_counter() - start_time) * 1000.0
        
        return GenerationResponse(
            output=response_text,
            finish_reason="stop" if not self._interrupted else "interrupted",
            token_usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split())
            },
            latency_ms=latency,
            provider="mock",
            model=model_name
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[GenerationResponse]:
        if not self._initialized:
            raise SwitchBoardError("Mock provider is not initialized.")
        
        model_name = request.metadata.get("model_name", "mock-llama3")
        if model_name not in self._models:
            raise SwitchBoardError(f"Model '{model_name}' not found.")
            
        model_obj = self._models[model_name]
        if model_obj.status != ModelStatus.LOADED:
            await self.load_model(model_name)

        self._interrupted = False
        prompt = request.inputs.get("prompt", "")
        chunks = [
            "Hello", "!", " I", " am", " a", " simulated", " response", 
            " from", " the", " SwitchBoard", " Mock", " Provider", "."
        ]

        # Async generator returning partial updates
        async def generator() -> AsyncIterator[GenerationResponse]:
            accumulated = ""
            start_time = time.perf_counter()
            for i, chunk in enumerate(chunks):
                if self._interrupted:
                    yield GenerationResponse(
                        output=accumulated,
                        finish_reason="interrupted",
                        token_usage={
                            "prompt_tokens": len(prompt.split()),
                            "completion_tokens": len(accumulated.split()),
                            "total_tokens": len(prompt.split()) + len(accumulated.split())
                        },
                        latency_ms=(time.perf_counter() - start_time) * 1000.0,
                        provider="mock",
                        model=model_name
                    )
                    break
                
                await asyncio.sleep(0.05)  # Simulate word stream delay
                accumulated += chunk
                
                yield GenerationResponse(
                    output=accumulated,
                    finish_reason=None if i < len(chunks) - 1 else "stop",
                    token_usage={
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(accumulated.split()),
                        "total_tokens": len(prompt.split()) + len(accumulated.split())
                    },
                    latency_ms=(time.perf_counter() - start_time) * 1000.0,
                    provider="mock",
                    model=model_name
                )
        return generator()

    async def interrupt(self) -> None:
        logger.info("Interrupting mock execution")
        self._interrupted = True
