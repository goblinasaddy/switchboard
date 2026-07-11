import asyncio
import json
import time
from typing import Any, AsyncIterator
import httpx
from switchboard.interfaces.provider import IProvider
from switchboard.types.runtime import Model, ModelCapability, ModelStatus, GenerationRequest, GenerationResponse
from switchboard.exceptions.base import SwitchBoardError
from switchboard.logging.config import get_logger

logger = get_logger("ollama_provider")

def _estimate_vram(parameter_size: str, quantization: str | None) -> float:
    """Heuristic estimator for model VRAM footprint in GB."""
    try:
        clean_size = "".join(c for c in parameter_size if c.isdigit() or c == ".")
        if not clean_size:
            raise ValueError("Invalid parameter size format")
        size_gb = float(clean_size)
        
        # default to 4-bit quantization if none specified
        bits = 4.0
        if quantization:
            q = quantization.upper()
            if "FP16" in q or "F16" in q:
                bits = 16.0
            elif "FP32" in q or "F32" in q:
                bits = 32.0
            elif "Q8" in q:
                bits = 8.0
            elif "Q5" in q:
                bits = 5.0
            elif "Q3" in q:
                bits = 3.0
                
        # (size * bits / 8) + 1.5GB overhead
        return round((size_gb * bits / 8.0) + 1.5, 1)
    except Exception:
        return 4.5


class OllamaProvider(IProvider):
    """
    Concrete implementation of IProvider interacting with local Ollama HTTP API.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None
        # Track active streaming response tasks for cancel/interruptions
        self._active_stream_requests: set[httpx.Response] = set()

    @property
    def name(self) -> str:
        return "ollama"

    async def initialize(self) -> None:
        """Initialize the async HTTP client."""
        logger.info("Initializing Ollama Provider", base_url=self._base_url)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=60.0)

    async def shutdown(self) -> None:
        """Close client and release connections."""
        logger.info("Shutting down Ollama Provider")
        await self.interrupt()
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health(self) -> bool:
        """Check if local Ollama server is reachable and active."""
        if not self._client:
            return False
        try:
            response = await self._client.get("/")
            return response.status_code == 200 and "Ollama is running" in response.text
        except Exception:
            return False

    async def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.CHAT,
            ModelCapability.STREAMING
        ]

    async def list_models(self) -> list[Model]:
        """Query local Ollama tags and parse them into SwitchBoard Models."""
        if not self._client:
            raise SwitchBoardError("Ollama provider is not initialized.")

        try:
            response = await self._client.get("/api/tags")
            if response.status_code != 200:
                raise SwitchBoardError(f"Ollama list tags failed with status {response.status_code}")
                
            data = response.json()
            models_data = data.get("models", [])
            models_list = []
            
            for md in models_data:
                details = md.get("details", {})
                param_size = details.get("parameter_size", "8B")
                quant = details.get("quantization_level")
                family = details.get("family", "unknown")
                
                vram_footprint = _estimate_vram(param_size, quant)
                
                # Check capability list
                caps = [ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING]
                if family in ("llama", "mistral", "gemma", "phi"):
                    caps.append(ModelCapability.CHAT)

                models_list.append(
                    Model(
                        name=md.get("name", md.get("model", "unknown")),
                        provider="ollama",
                        family=family,
                        quantization=quant,
                        context_length=8192,  # default context fallback
                        estimated_vram_gb=vram_footprint,
                        capabilities=caps,
                        status=ModelStatus.UNLOADED,
                        metadata={"details": details}
                    )
                )
            return models_list
        except httpx.RequestError as e:
            raise SwitchBoardError(f"HTTP request to Ollama failed: {e}") from e
        except Exception as e:
            raise SwitchBoardError(f"Failed to parse Ollama models list: {e}") from e

    async def load_model(self, name: str) -> None:
        """
        Force load a model into memory by executing a blank generation request 
        with keep_alive set to -1 (keep loaded).
        """
        if not self._client:
            raise SwitchBoardError("Ollama provider is not initialized.")
            
        logger.info("Loading model into memory via Ollama", model=name)
        try:
            payload = {
                "model": name,
                "prompt": "",
                "keep_alive": -1  # keeps the model loaded in memory
            }
            response = await self._client.post("/api/generate", json=payload, timeout=120.0)
            if response.status_code != 200:
                raise SwitchBoardError(f"Failed to load model {name}. status: {response.status_code}")
        except Exception as e:
            raise SwitchBoardError(f"Error loading model '{name}' through Ollama: {e}") from e

    async def unload_model(self, name: str) -> None:
        """
        Unload model from memory by executing a blank generation request 
        with keep_alive set to 0.
        """
        if not self._client:
            raise SwitchBoardError("Ollama provider is not initialized.")
            
        logger.info("Unloading model from memory via Ollama", model=name)
        try:
            payload = {
                "model": name,
                "prompt": "",
                "keep_alive": 0  # immediately unloads the model
            }
            response = await self._client.post("/api/generate", json=payload, timeout=10.0)
            if response.status_code != 200:
                raise SwitchBoardError(f"Failed to unload model {name}. status: {response.status_code}")
        except Exception as e:
            raise SwitchBoardError(f"Error unloading model '{name}' through Ollama: {e}") from e

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute a complete generation task on Ollama."""
        if not self._client:
            raise SwitchBoardError("Ollama provider is not initialized.")

        model_name = request.metadata.get("model_name")
        if not model_name:
            raise SwitchBoardError("Generation request is missing target 'model_name' metadata.")

        prompt = request.inputs.get("prompt", "")
        system_prompt = request.inputs.get("system_prompt")
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": request.options
        }
        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.perf_counter()
        try:
            response = await self._client.post("/api/generate", json=payload)
            if response.status_code != 200:
                raise SwitchBoardError(f"Ollama generation failed with status {response.status_code}: {response.text}")
                
            res_json = response.json()
            latency = (time.perf_counter() - start_time) * 1000.0
            
            # Extract token statistics (nanoseconds -> ms)
            p_eval = res_json.get("prompt_eval_count", 0)
            eval_count = res_json.get("eval_count", 0)
            
            return GenerationResponse(
                output=res_json.get("response", ""),
                finish_reason="stop" if res_json.get("done", False) else "unknown",
                token_usage={
                    "prompt_tokens": p_eval,
                    "completion_tokens": eval_count,
                    "total_tokens": p_eval + eval_count
                },
                latency_ms=latency,
                provider="ollama",
                model=model_name,
                metadata=res_json
            )
        except httpx.RequestError as e:
            raise SwitchBoardError(f"HTTP request to Ollama generate failed: {e}") from e
        except Exception as e:
            raise SwitchBoardError(f"Error running Ollama generation: {e}") from e

    async def stream(self, request: GenerationRequest) -> AsyncIterator[GenerationResponse]:
        """Execute streaming generation returning an async iterator."""
        if not self._client:
            raise SwitchBoardError("Ollama provider is not initialized.")

        model_name = request.metadata.get("model_name")
        if not model_name:
            raise SwitchBoardError("Generation request is missing target 'model_name' metadata.")

        prompt = request.inputs.get("prompt", "")
        system_prompt = request.inputs.get("system_prompt")

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": request.options
        }
        if system_prompt:
            payload["system"] = system_prompt

        async def stream_generator() -> AsyncIterator[GenerationResponse]:
            accumulated_output = ""
            start_time = time.perf_counter()
            
            # Using httpx stream interface
            try:
                # We need to construct a new AsyncClient or request directly
                req = self._client.build_request("POST", "/api/generate", json=payload)
                response = await self._client.send(req, stream=True)
                self._active_stream_requests.add(response)
                
                try:
                    if response.status_code != 200:
                        await response.aread()  # Consume body to release connection
                        raise SwitchBoardError(f"Ollama stream failed with status {response.status_code}")
                        
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        chunk_json = json.loads(line)
                        accumulated_output += chunk_json.get("response", "")
                        done = chunk_json.get("done", False)
                        
                        p_eval = chunk_json.get("prompt_eval_count", 0)
                        eval_count = chunk_json.get("eval_count", 0)
                        
                        yield GenerationResponse(
                            output=accumulated_output,
                            finish_reason="stop" if done else None,
                            token_usage={
                                "prompt_tokens": p_eval,
                                "completion_tokens": eval_count,
                                "total_tokens": p_eval + eval_count
                            },
                            latency_ms=(time.perf_counter() - start_time) * 1000.0,
                            provider="ollama",
                            model=model_name,
                            metadata=chunk_json
                        )
                finally:
                    self._active_stream_requests.discard(response)
                    await response.aclose()
            except httpx.RequestError as e:
                raise SwitchBoardError(f"HTTP stream to Ollama failed: {e}") from e
            except asyncio.CancelledError:
                logger.info("Streaming request task cancelled")
                # We raise CancelledError to let ComputeSession log/handle it
                raise
            except Exception as e:
                raise SwitchBoardError(f"Error parsing Ollama stream chunk: {e}") from e

        return stream_generator()

    async def interrupt(self) -> None:
        """Interrupt any active streaming connections by closing their sockets."""
        if self._active_stream_requests:
            logger.info("Interrupting active Ollama streaming requests", count=len(self._active_stream_requests))
            for res in list(self._active_stream_requests):
                try:
                    await res.aclose()
                except Exception as e:
                    logger.warning("Error closing stream during interrupt", error=str(e))
            self._active_stream_requests.clear()
