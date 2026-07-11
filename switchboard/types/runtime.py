from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class ModelCapability(str, Enum):
    """
    Capabilities supported by an inference model or provider.
    """
    TEXT_GENERATION = "TEXT_GENERATION"
    CHAT = "CHAT"
    EMBEDDINGS = "EMBEDDINGS"
    TOOLS = "TOOLS"
    VISION = "VISION"
    AUDIO = "AUDIO"
    STREAMING = "STREAMING"
    JSON_OUTPUT = "JSON_OUTPUT"
    FUNCTION_CALLING = "FUNCTION_CALLING"


class ModelStatus(str, Enum):
    """
    Activation status of a model inside the SwitchBoard platform.
    """
    LOADED = "LOADED"
    UNLOADED = "UNLOADED"
    LOADING = "LOADING"
    ERROR = "ERROR"


class Model(BaseModel):
    """
    Canonical metadata representing a model resource managed by the platform.
    """
    name: str = Field(description="Unique model identifier (e.g. 'llama3:8b').")
    provider: str = Field(description="Identifier of the provider owning this model.")
    family: str = Field(description="Model lineage family (e.g. 'llama', 'mistral').")
    quantization: str | None = Field(default=None, description="Quantization format (e.g. 'Q4_K_M', 'FP16').")
    context_length: int = Field(description="Maximum context window length in tokens.")
    estimated_vram_gb: float = Field(description="Estimated GPU VRAM footprint in Gigabytes.")
    capabilities: list[ModelCapability] = Field(default_factory=list, description="List of capabilities supported.")
    status: ModelStatus = Field(default=ModelStatus.UNLOADED, description="Current loading status.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional model parameters or info.")


class GenerationRequest(BaseModel):
    """
    Canonical package for model generation requests, cleanly separating
    raw inputs from execution configurations.
    """
    inputs: dict[str, Any] = Field(
        description="Structured request inputs (e.g., {'prompt': 'hello', 'system_prompt': 'you are a helper'})."
    )
    attachments: list[Any] = Field(
        default_factory=list, 
        description="Non-prompt inputs (e.g., images, document objects, parsed symbols)."
    )
    options: dict[str, Any] = Field(
        default_factory=dict, 
        description="Inference configurations (e.g. {'temperature': 0.7, 'max_tokens': 100})."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, 
        description="Execution tracking metadata."
    )


class GenerationResponse(BaseModel):
    """
    Canonical package for model generation outputs.
    """
    output: Any = Field(description="Output payload (text, tool calls, JSON, or embeddings).")
    finish_reason: str | None = Field(default=None, description="Reason for stopping (e.g. 'stop', 'length').")
    token_usage: dict[str, int] = Field(
        default_factory=dict, 
        description="Token statistics (e.g. {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30})."
    )
    latency_ms: float = Field(description="Generation duration in milliseconds.")
    provider: str = Field(description="Backend provider that executed the request.")
    model: str = Field(description="Name of the model executing the request.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional statistics or metrics.")
