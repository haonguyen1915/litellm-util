"""Azure OpenAI provider and models."""

from llm_cli.providers.base import create_model, create_provider

AZURE_MODELS = [
    create_model(
        id="azure/gpt-4o",
        provider="azure",
        context_window=128_000,
        max_output=16_384,
        input_price=2.50,
        output_price=10.00,
        capabilities=["vision", "tools", "streaming", "json_mode"],
        training_cutoff="October 2023",
    ),
    create_model(
        id="azure/gpt-4o-mini",
        provider="azure",
        context_window=128_000,
        max_output=16_384,
        input_price=0.15,
        output_price=0.60,
        capabilities=["vision", "tools", "streaming", "json_mode"],
        training_cutoff="October 2023",
    ),
    create_model(
        id="azure/gpt-4-turbo",
        provider="azure",
        context_window=128_000,
        max_output=4_096,
        input_price=10.00,
        output_price=30.00,
        capabilities=["vision", "tools", "streaming", "json_mode"],
        training_cutoff="December 2023",
    ),
    create_model(
        id="azure/gpt-4",
        provider="azure",
        context_window=8_192,
        max_output=4_096,
        input_price=30.00,
        output_price=60.00,
        capabilities=["tools", "streaming"],
        training_cutoff="September 2021",
    ),
    create_model(
        id="azure/gpt-35-turbo",
        provider="azure",
        context_window=16_385,
        max_output=4_096,
        input_price=0.50,
        output_price=1.50,
        capabilities=["tools", "streaming"],
        training_cutoff="September 2021",
    ),
]

AZURE_PROVIDER = create_provider(
    id="azure",
    name="Azure OpenAI",
    description="Azure OpenAI Service",
    models=AZURE_MODELS,
    env_var="AZURE_API_KEY",
)
