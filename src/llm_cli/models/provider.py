"""Provider and model information schemas."""

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Information about a model."""

    id: str
    provider: str
    context_window: int
    max_output: int
    input_price: float  # per 1M tokens
    output_price: float  # per 1M tokens
    capabilities: list[str] = Field(default_factory=list)
    training_cutoff: str | None = None


class ProviderInfo(BaseModel):
    """Information about a provider."""

    id: str
    name: str
    description: str
    models: list[ModelInfo] = Field(default_factory=list)
    requires_api_key: bool = True
    env_var: str | None = None  # Environment variable for API key
