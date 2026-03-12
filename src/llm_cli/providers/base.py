"""Base provider class and utilities."""

from llm_cli.models.provider import ModelInfo, ProviderInfo


def create_provider(
    id: str,
    name: str,
    description: str,
    models: list[ModelInfo],
    env_var: str | None = None,
    requires_api_key: bool = True,
) -> ProviderInfo:
    """Helper function to create a ProviderInfo.

    Args:
        id: Provider identifier.
        name: Display name.
        description: Short description.
        models: List of supported models.
        env_var: Environment variable for API key.
        requires_api_key: Whether API key is required.

    Returns:
        ProviderInfo object.
    """
    return ProviderInfo(
        id=id,
        name=name,
        description=description,
        models=models,
        env_var=env_var,
        requires_api_key=requires_api_key,
    )


def create_model(
    id: str,
    provider: str,
    context_window: int,
    max_output: int,
    input_price: float,
    output_price: float,
    capabilities: list[str] | None = None,
    training_cutoff: str | None = None,
) -> ModelInfo:
    """Helper function to create a ModelInfo.

    Args:
        id: Model identifier.
        provider: Provider name.
        context_window: Context window size in tokens.
        max_output: Maximum output tokens.
        input_price: Input price per 1M tokens.
        output_price: Output price per 1M tokens.
        capabilities: List of capabilities (e.g., 'vision', 'tools').
        training_cutoff: Training data cutoff date.

    Returns:
        ModelInfo object.
    """
    return ModelInfo(
        id=id,
        provider=provider,
        context_window=context_window,
        max_output=max_output,
        input_price=input_price,
        output_price=output_price,
        capabilities=capabilities or [],
        training_cutoff=training_cutoff,
    )
