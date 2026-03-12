"""Mistral AI provider and models."""

from llm_cli.providers.base import create_model, create_provider

MISTRAL_MODELS = [
    create_model(
        id="mistral/mistral-large-latest",
        provider="mistral",
        context_window=128_000,
        max_output=8_192,
        input_price=2.00,
        output_price=6.00,
        capabilities=["tools", "streaming", "json_mode"],
        training_cutoff="November 2024",
    ),
    create_model(
        id="mistral/mistral-medium-latest",
        provider="mistral",
        context_window=32_000,
        max_output=8_192,
        input_price=2.70,
        output_price=8.10,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="mistral/mistral-small-latest",
        provider="mistral",
        context_window=32_000,
        max_output=8_192,
        input_price=0.20,
        output_price=0.60,
        capabilities=["tools", "streaming", "json_mode"],
    ),
    create_model(
        id="mistral/codestral-latest",
        provider="mistral",
        context_window=32_000,
        max_output=8_192,
        input_price=0.20,
        output_price=0.60,
        capabilities=["streaming", "fill_in_middle"],
    ),
    create_model(
        id="mistral/pixtral-large-latest",
        provider="mistral",
        context_window=128_000,
        max_output=8_192,
        input_price=2.00,
        output_price=6.00,
        capabilities=["vision", "tools", "streaming"],
    ),
    create_model(
        id="mistral/open-mixtral-8x22b",
        provider="mistral",
        context_window=64_000,
        max_output=8_192,
        input_price=2.00,
        output_price=6.00,
        capabilities=["tools", "streaming"],
    ),
]

MISTRAL_PROVIDER = create_provider(
    id="mistral",
    name="Mistral AI",
    description="Mistral AI (Mistral, Codestral, Pixtral)",
    models=MISTRAL_MODELS,
    env_var="MISTRAL_API_KEY",
)
