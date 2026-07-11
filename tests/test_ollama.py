import os
import asyncio
from unittest import mock
import pytest
import httpx
from switchboard.compute.adapters.ollama import OllamaProvider, _estimate_vram
from switchboard.types.runtime import (
    GenerationRequest,
    ModelStatus,
    ModelCapability,
)
from switchboard.exceptions.base import SwitchBoardError

# 1. Heuristic unit tests
def test_estimate_vram() -> None:
    # 8B model with Q4 (default) -> 8.0 * 4 / 8 + 1.5 = 5.5
    assert _estimate_vram("8B", None) == 5.5
    
    # 7B model with FP16 -> 7.0 * 16 / 8 + 1.5 = 15.5
    assert _estimate_vram("7B", "FP16") == 15.5
    
    # 70B model with Q8 -> 70.0 * 8 / 8 + 1.5 = 71.5
    assert _estimate_vram("70B", "Q8") == 71.5
    
    # Fallback default
    assert _estimate_vram("broken", "broken") == 4.5


# 2. Mocked provider tests
@pytest.mark.asyncio
async def test_ollama_list_models_mocked() -> None:
    provider = OllamaProvider()
    await provider.initialize()

    # Mock response for /api/tags
    mock_tags_response = {
        "models": [
            {
                "name": "llama3:8b",
                "details": {
                    "family": "llama",
                    "parameter_size": "8B",
                    "quantization_level": "Q4_0"
                }
            }
        ]
    }

    # Patch the HTTP client request
    with mock.patch.object(provider._client, "get") as mock_get:
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_tags_response
        mock_get.return_value = mock_resp

        models = await provider.list_models()
        assert len(models) == 1
        assert models[0].name == "llama3:8b"
        assert models[0].family == "llama"
        assert models[0].quantization == "Q4_0"
        assert ModelCapability.CHAT in models[0].capabilities
        assert models[0].estimated_vram_gb == 5.5

    await provider.shutdown()


@pytest.mark.asyncio
async def test_ollama_generate_mocked() -> None:
    provider = OllamaProvider()
    await provider.initialize()

    mock_generate_response = {
        "response": "Hello world",
        "done": True,
        "prompt_eval_count": 5,
        "eval_count": 10,
        "total_duration": 100_000_000  # 100ms in nanoseconds
    }

    with mock.patch.object(provider._client, "post") as mock_post:
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_generate_response
        mock_post.return_value = mock_resp

        request = GenerationRequest(
            inputs={"prompt": "hi"},
            metadata={"model_name": "llama3:8b"}
        )
        response = await provider.generate(request)
        
        assert response.output == "Hello world"
        assert response.finish_reason == "stop"
        assert response.token_usage["prompt_tokens"] == 5
        assert response.token_usage["completion_tokens"] == 10
        assert response.latency_ms > 0.0

    await provider.shutdown()


# 3. Live integration tests (skipped if Ollama is not active)
async def _is_ollama_online() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("http://localhost:11434/")
            return res.status_code == 200 and "Ollama is running" in res.text
    except Exception:
        return False

# Detect online state for skip condition
OLLAMA_ONLINE = asyncio.run(_is_ollama_online()) if "asyncio" in globals() or True else False

@pytest.mark.skipif(not OLLAMA_ONLINE, reason="Local Ollama server is not running at localhost:11434")
@pytest.mark.asyncio
async def test_ollama_live_health() -> None:
    provider = OllamaProvider()
    await provider.initialize()
    
    assert await provider.health() is True
    
    await provider.shutdown()


@pytest.mark.skipif(not OLLAMA_ONLINE, reason="Local Ollama server is not running at localhost:11434")
@pytest.mark.asyncio
async def test_ollama_live_list_models() -> None:
    provider = OllamaProvider()
    await provider.initialize()
    
    models = await provider.list_models()
    # If healthy, it should at least return a list (even if empty)
    assert isinstance(models, list)
    
    await provider.shutdown()
